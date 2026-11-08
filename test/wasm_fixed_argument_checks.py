"""Complete packed parameter images and validated copy/cleanup controls."""
from pathlib import Path
import json
import re
from wasm_data_iteration_checks import function_span
ROOT = Path(__file__).resolve().parents[1]


def check_images(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        module = out / f'wasm_fixed_argument_owner-O{opt}.wasm'
        text = run([validator, 'print', module]).stdout.decode()
        def emit(name, value):
            value = value[:value.rfind(')')] + '  (export "test_stack_top_0" (global 0))\n)\n'
            wat = out / f'fixed-argument-{name}-O{opt}.wat'; wasm = wat.with_suffix('.wasm')
            wat.write_text(value)
            run([validator, 'parse', wat, '-o', wasm]); run([validator, 'validate', wasm])
            return wasm
        healthy = emit('image', text)
        metadata = out / f'fixed-argument-image-O{opt}.json'
        result = run([node, ROOT / 'test/wasm_fixed_argument_owner.mjs', healthy, metadata])
        assert result.stdout == b'arg-live\ncallee-live\ncallee-defer\ndone\n' and not result.stderr
        count += 1
        a, z = function_span(text, 'consume'); body = text[a:z]
        length = r'i32.const 9(?=\s+memory.copy(?: 0 0)?\s)'
        assert len(re.findall(length, body)) == 1
        for name, value in [('short', '8'), ('long', '10')]:
            changed = re.sub(length, 'i32.const ' + value, body)
            damaged = emit(name, text[:a] + changed + text[z:])
            result = run([node, ROOT / 'test/wasm_fixed_argument_owner.mjs', damaged], ok=False)
            assert result.returncode == 1 and b'fixed argument callee image differs' in result.stderr, (name, result.stderr)
            count += 1
        changed, n = re.subn(r'(?m)^(\s*)memory.copy(?: 0 0)?\s*$',
                              r'\1drop\n\1drop\n\1drop', body, count=1)
        assert n == 1
        damaged = emit('omitted', text[:a] + changed + text[z:])
        result = run([node, ROOT / 'test/wasm_fixed_argument_owner.mjs', damaged], ok=False)
        assert result.returncode == 1 and b'fixed argument callee image differs' in result.stderr
        count += 1
        a, z = function_span(text, 'main'); body = text[a:z]
        arguments = list(re.finditer(r'(?m)(^\s*local.get \S+\s*\n)(\s*local.get \S+\s*\n)(\s*call \$consume\.\d+\s*$)', body))
        assert len(arguments) == 1
        match = arguments[0]
        source = json.loads(metadata.read_text())['source']
        changed = body[:match.start(1)] + f'    i32.const {source}\n' + body[match.end(1):]
        damaged = emit('original-source', text[:a] + changed + text[z:])
        result = run([node, ROOT / 'test/wasm_fixed_argument_owner.mjs', damaged], ok=False)
        assert result.returncode == 1 and b'fixed argument callee image differs' in result.stderr
        count += 1
        changed, n = re.subn(r'(?m)^(\s*)global.set (?:0|\$[^\s]+)\s*$', r'\1drop', body, count=1)
        assert n == 1
        damaged = emit('missing-restore', text[:a] + changed + text[z:])
        result = run([node, ROOT / 'test/wasm_fixed_argument_owner.mjs', damaged], ok=False)
        assert result.returncode == 1 and b'fixed argument live frame top differs' in result.stderr
        count += 1
    return count


def check_aliases(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        module = out / f'wasm_fixed_argument_isolation-O{opt}.wasm'
        healthy = run([node, ROOT / 'scripts/run_wasm.mjs', module])
        assert healthy.stdout == b'isolation\n' and not healthy.stderr
        count += 1
        text = run([validator, 'print', module]).stdout.decode()
        a, z = function_span(text, 'read')
        body, n = re.subn(r'i32.const 8(?=\s+i32.add)', 'i32.const 0', text[a:z])
        assert n >= 2
        wat = out / f'fixed-argument-aliased-parameters-O{opt}.wat'; wasm = wat.with_suffix('.wasm')
        wat.write_text(text[:a] + body + text[z:])
        run([validator, 'parse', wat, '-o', wasm]); run([validator, 'validate', wasm])
        result = run([node, ROOT / 'scripts/run_wasm.mjs', wasm], ok=False)
        assert result.returncode == 1 and b'assert failed' in result.stderr and not result.stdout
        count += 1
    return count


def check_guards(run, exe, cc, out, node, validator, wasmtime_python):
    cases = [
        ('empty', 'enum E{Empty,Value{n:i64}}\n'
         'recursive fn take(x:E.Empty)->i64{print("inside");return 1;}\n'
         'fn main(){var x:E.Empty=default<E.Empty>();print(take(x));}\n',
         None, True),
        ('frame-sum', 'struct Huge{bytes:u8[2147483648]}\n'
         'recursive fn take(a:Huge,b:Huge)->i64{return a.bytes[0]+b.bytes[0];}\n'
         'fn main(){var x:Huge=default<Huge>();print(take(x,x));}\n',
         b'frame exceeds memory32', False),
    ]
    count = 0
    for name, text, reason, execute in cases:
        source = out / f'fixed-argument-{name}-guard.goose'; source.write_text(text)
        for opt in (0, 2):
            prefix = out / f'fixed-argument-{name}-guard-O{opt}'
            c, native, module = (prefix.with_suffix(ext) for ext in ('.c', '.native', '.wasm'))
            run([exe, f'-O{opt}', '--standalone', '-o', c, source])
            if execute:
                run([cc, c, '-pthread', '-lm', '-ldl', '-o', native])
                reference = run([native])
                assert reference.stdout == b'inside\n1\n' and not reference.stderr
            # Huge declarations are frontend/C-emission checks only.
            # Do not build or execute their native images or instantiate Wasm.
            module.unlink(missing_ok=True)
            if name == 'empty':
                from wasm_zero_call_checks import check_completed
                check_completed(run, exe, source, module, opt, reference.stdout, node, validator, wasmtime_python)
                count += 1
                continue
            result = run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, source], ok=False)
            assert result.returncode == 1 and reason in result.stderr and not module.exists(), (name, result.stderr)
            count += 1
    return count


def check_dynamic(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        module = out / f'wasm_fixed_argument_dynamic_base-O{opt}.wasm'
        text = run([validator, 'print', module]).stdout.decode()
        a, z = function_span(text, 'read')
        assert re.search(r'\(param\s+i32\s+i32\)', text[a:z])
        def emit(name, value):
            exports = ''.join(f'  (export "test_stack_top_{i}" (global {i}))\n' for i in range(3))
            value = value[:value.rfind(')')] + exports + ')\n'
            wat = out / f'fixed-argument-dynamic-{name}-O{opt}.wat'; wasm = wat.with_suffix('.wasm')
            wat.write_text(value)
            run([validator, 'parse', wat, '-o', wasm]); run([validator, 'validate', wasm])
            return wasm
        healthy = emit('owner', text)
        result = run([node, ROOT / 'test/wasm_fixed_argument_dynamic.mjs', healthy])
        assert result.stdout == b'inside\ninside\ndynamic_base\n' and not result.stderr
        count += 1
        a, z = function_span(text, 'main')
        changed, n = re.subn(r'i32.const 1(?=\s+call \$read\.\d+\s)', 'i32.const 0', text[a:z])
        assert n == 1
        damaged = emit('wrong-base', text[:a] + changed + text[z:])
        result = run([node, ROOT / 'test/wasm_fixed_argument_dynamic.mjs', damaged], ok=False)
        assert result.returncode == 1 and b'fixed argument dynamic memory base differs' in result.stderr
        assert result.stdout == b'inside\n'
        count += 1
    return count
