"""Protected caller results, return-before-defer images and valid fault controls."""
from pathlib import Path
import json
import re
from wasm_data_iteration_checks import function_span
ROOT = Path(__file__).resolve().parents[1]


def check_images(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        module = out / f'wasm_array_result_owner-O{opt}.wasm'
        text = run([validator, 'print', module]).stdout.decode()
        def emit(name, value):
            value = value[:value.rfind(')')] + '  (export "test_stack_top_0" (global 0))\n)\n'
            wat = out / f'array-result-{name}-O{opt}.wat'; wasm = wat.with_suffix('.wasm')
            wat.write_text(value)
            run([validator, 'parse', wat, '-o', wasm]); run([validator, 'validate', wasm])
            return wasm
        healthy = emit('owner', text)
        metadata = out / f'array-result-owner-O{opt}.json'
        result = run([node, ROOT / 'test/wasm_array_result_owner.mjs', healthy, metadata])
        assert result.stdout == b'before\narg-live\ncallee-live\ndefer\nafter\n' and not result.stderr
        count += 1
        a, z = function_span(text, 'make'); body = text[a:z]
        lengths = list(re.finditer(r'i32.const 9(?=\s+local.set \S+\s)', body))
        assert len(lengths) == 2
        span = lengths[-1]
        damaged_bodies = [(name, body[:span.start()] + 'i32.const ' + value + body[span.end():])
                          for name, value in [('short', '8'), ('long', '10')]]
        copies = list(re.finditer(r'(?m)^(\s*)memory.copy(?: 0 0)?\s*$', body))
        assert len(copies) == 3
        last = copies[-1]
        damaged_bodies.append(('omitted', body[:last.start()] + '    drop\n    drop\n    drop' + body[last.end():]))
        redirected, n = re.subn(r'(?m)^(\s*)local.get 2\s*$', r'\1local.get 3', body)
        assert n == 1
        damaged_bodies.append(('callee-destination', redirected))
        for name, modified in damaged_bodies:
            damaged = emit(name, text[:a] + modified + text[z:])
            result = run([node, ROOT / 'test/wasm_array_result_owner.mjs', damaged], ok=False)
            assert result.returncode == 1 and b'array result protected image differs' in result.stderr, (name, result.stderr)
            count += 1
        a, z = function_span(text, 'main'); body = text[a:z]
        arguments = list(re.finditer(r'(?m)(^\s*local.get \S+\s*\n)(\s*local.get \S+\s*\n)(\s*local.get \S+\s*\n)(\s*call \$make\.\d+\s*$)', body))
        assert len(arguments) == 1
        match = arguments[0]; target = json.loads(metadata.read_text())['target']
        modified = body[:match.start(3)] + f'    i32.const {target}\n' + body[match.end(3):]
        damaged = emit('early-target', text[:a] + modified + text[z:])
        result = run([node, ROOT / 'test/wasm_array_result_owner.mjs', damaged], ok=False)
        assert result.returncode == 1 and b'array result protected image differs' in result.stderr
        count += 1
        restores = list(re.finditer(r'(?m)^\s*global.set (?:0|\$[^\s]+)\s*$', body))
        assert len(restores) == 2
        last = restores[-1]
        modified = body[:last.start()] + '    drop' + body[last.end():]
        damaged = emit('missing-restore', text[:a] + modified + text[z:])
        result = run([node, ROOT / 'test/wasm_array_result_owner.mjs', damaged], ok=False)
        assert result.returncode == 1 and b'array result live frame top differs' in result.stderr
        count += 1
    return count


def check_guards(run, exe, cc, out, node, validator, wasmtime_python):
    cases = [
        ('empty', 'recursive fn make()->u8[0]{print("inside");return default<u8[0]>();}\n'
         'fn main(){var a:u8[0]=make();print(a.len);}\n', b'inside\n0\n',
         None),
        ('adaptation', 'recursive fn make()->u8[2]{return[3,4];}\n'
         'fn main(){var a:u8[..3]=make();print(a.len);}\n', b'2\n',
         b'aggregate result adaptation needs the pending destination lowering'),
        ('nonfixed', 'recursive fn make()->u8[]{var a:u8[]=[3,4];return a;}\n'
         'fn main(){var a:u8[]=make();print(a[1]);}\n', b'4\n',
         b'array results need the pending destination lowering'),
    ]
    count = 0
    for name, text, expected, reason in cases:
        source = out / f'array-result-{name}-guard.goose'; source.write_text(text)
        for opt in (0, 2):
            prefix = out / f'array-result-{name}-guard-O{opt}'
            c, native, module = (prefix.with_suffix(ext) for ext in ('.c', '.native', '.wasm'))
            run([exe, f'-O{opt}', '--standalone', '-o', c, source])
            run([cc, c, '-pthread', '-lm', '-ldl', '-o', native])
            reference = run([native]); assert reference.stdout == expected and not reference.stderr
            module.unlink(missing_ok=True)
            if name == 'empty':
                from wasm_zero_call_checks import check_completed
                check_completed(run, exe, source, module, opt, reference.stdout, node, validator, wasmtime_python)
                count += 1
                continue
            result = run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, source], ok=False)
            assert result.returncode == 1 and reason in result.stderr, (name, result.stderr)
            assert not module.exists()
            count += 1
    return count


def check_failures(run, exe, cc, node, validator, out):
    cases = [
        ('division', 'var target:i64[2]=[1,2];var divisor:i64=0;\n'
         'recursive fn make()->i64[2]{return[9,8/divisor];}\n'
         'fn main(){print("before");target=make();print("after");}\n', b'division by zero'),
        ('bounds', 'struct H{items:i64[2]}\nvar index:i64=1;\n'
         'recursive fn make()->i64[2]{print("rhs");return[7,8];}\n'
         'fn main(){var rows:H[]=[H{items:[1,2]}];print("before");'
         'rows[index].items=make();print("after");}\n', b'index 1 out of bounds (length 1)'),
    ]
    count = 0
    for name, text, reason in cases:
        source = out / f'array-result-{name}-failure.goose'; source.write_text(text)
        for opt in (0, 2):
            prefix = out / f'array-result-{name}-failure-O{opt}'
            c, native, module = (prefix.with_suffix(ext) for ext in ('.c', '.native', '.wasm'))
            run([exe, f'-O{opt}', '--standalone', '-o', c, source])
            run([cc, c, '-pthread', '-lm', '-ldl', '-o', native])
            reference = run([native], ok=False)
            assert reference.returncode != 0 and reference.stdout == b'before\n' and reason in reference.stderr
            run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, source])
            text = run([validator, 'print', module]).stdout.decode()
            text = text[:text.rfind(')')] + '  (export "test_stack_top_0" (global 0))\n)\n'
            wat = prefix.with_suffix('.wat'); wat.write_text(text)
            checked = out / f'array-result-{name}-observed-O{opt}.wasm'
            run([validator, 'parse', wat, '-o', checked]); run([validator, 'validate', checked])
            result = run([node, ROOT / 'test/wasm_constructor_assignment_failure.mjs', checked, name])
            assert result.stdout == b'before\n' and not result.stderr
            count += 1
    return count


def check_data(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        module = out / f'wasm_array_result_data_control-O{opt}.wasm'
        text = run([validator, 'print', module]).stdout.decode()
        def emit(name, value):
            exports = ''.join(f'  (export "test_stack_top_{i}" (global {i}))\n' for i in range(3))
            wat = out / f'array-result-data-{name}-O{opt}.wat'; wasm = wat.with_suffix('.wasm')
            wat.write_text(value[:value.rfind(')')] + exports + ')\n')
            run([validator, 'parse', wat, '-o', wasm]); run([validator, 'validate', wasm])
            return wasm
        healthy = emit('owner', text)
        result = run([node, ROOT / 'test/wasm_array_result_data.mjs', healthy])
        assert result.stdout == b'row0\nrow1\nrow2\ndata_control\n' and not result.stderr
        count += 1
        a, z = function_span(text, 'main'); body = text[a:z]
        stores = list(re.finditer(r'i64\.store8 1 offset=5\b', body))
        assert len(stores) == 3, len(stores)
        wrong_width, n = re.subn(r'i64\.store8 1 offset=5\b', 'i64.store16 1 offset=5', body)
        assert n == 3
        last = stores[-1]
        changed = [('width', wrong_width),
                   ('omitted', body[:last.start()] + 'drop\n    drop' + body[last.end():]),
                   ('namespace', body[:last.start()] + 'i64.store8 2 offset=5' + body[last.end():])]
        for name, modified in changed:
            damaged = emit(name, text[:a] + modified + text[z:])
            result = run([node, ROOT / 'test/wasm_array_result_data.mjs', damaged], ok=False)
            assert result.returncode == 1 and b'nested array data image differs' in result.stderr, (name, result.stderr)
            count += 1
    return count
