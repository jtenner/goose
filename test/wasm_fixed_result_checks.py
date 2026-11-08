"""Protected caller results, return-before-defer images and valid fault controls."""
from pathlib import Path
import json
import re
from wasm_data_iteration_checks import function_span
ROOT = Path(__file__).resolve().parents[1]


def check_images(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        module = out / f'wasm_fixed_result_owner-O{opt}.wasm'
        text = run([validator, 'print', module]).stdout.decode()
        def emit(name, value):
            value = value[:value.rfind(')')] + '  (export "test_stack_top_0" (global 0))\n)\n'
            wat = out / f'fixed-result-{name}-O{opt}.wat'; wasm = wat.with_suffix('.wasm')
            wat.write_text(value)
            run([validator, 'parse', wat, '-o', wasm]); run([validator, 'validate', wasm])
            return wasm
        healthy = emit('owner', text)
        metadata = out / f'fixed-result-owner-O{opt}.json'
        result = run([node, ROOT / 'test/wasm_fixed_result_owner.mjs', healthy, metadata])
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
            result = run([node, ROOT / 'test/wasm_fixed_result_owner.mjs', damaged], ok=False)
            assert result.returncode == 1 and b'fixed result protected image differs' in result.stderr, (name, result.stderr)
            count += 1
        a, z = function_span(text, 'main'); body = text[a:z]
        arguments = list(re.finditer(r'(?m)(^\s*local.get \S+\s*\n)(\s*local.get \S+\s*\n)(\s*local.get \S+\s*\n)(\s*call \$make\.\d+\s*$)', body))
        assert len(arguments) == 1
        match = arguments[0]; target = json.loads(metadata.read_text())['target']
        modified = body[:match.start(3)] + f'    i32.const {target}\n' + body[match.end(3):]
        damaged = emit('early-target', text[:a] + modified + text[z:])
        result = run([node, ROOT / 'test/wasm_fixed_result_owner.mjs', damaged], ok=False)
        assert result.returncode == 1 and b'fixed result protected image differs' in result.stderr
        count += 1
        restores = list(re.finditer(r'(?m)^\s*global.set (?:0|\$[^\s]+)\s*$', body))
        assert len(restores) == 2
        last = restores[-1]
        modified = body[:last.start()] + '    drop' + body[last.end():]
        damaged = emit('missing-restore', text[:a] + modified + text[z:])
        result = run([node, ROOT / 'test/wasm_fixed_result_owner.mjs', damaged], ok=False)
        assert result.returncode == 1 and b'fixed result live frame top differs' in result.stderr
        count += 1
    return count


def check_guards(run, exe, cc, out):
    source = out / 'fixed-result-empty-guard.goose'
    source.write_text('enum E{Empty,Value{n:i64}}\n'
                      'recursive fn make()->E.Empty{return default<E.Empty>();}\n'
                      'fn main(){var x:E.Empty=make();assert(x .== &x);print("empty_result");}\n')
    count = 0
    for opt in (0, 2):
        prefix = out / f'fixed-result-empty-guard-O{opt}'
        c, native, module = (prefix.with_suffix(ext) for ext in ('.c', '.native', '.wasm'))
        run([exe, f'-O{opt}', '--standalone', '-o', c, source])
        run([cc, c, '-pthread', '-lm', '-ldl', '-o', native])
        reference = run([native]); assert reference.stdout == b'empty_result\n' and not reference.stderr
        module.unlink(missing_ok=True)
        result = run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, source], ok=False)
        assert result.returncode == 1 and b'zero-sized aggregate results need the pending call lowering' in result.stderr
        assert not module.exists()
        count += 1
    return count


def check_failure(run, exe, cc, node, validator, out):
    source = out / 'fixed-result-failure.goose'
    source.write_text('struct S { a:i64, b:i64 }\n'
                      'var target:S = S { a:1, b:2 };\n'
                      'var divisor:i64 = 0;\n'
                      'recursive fn make()->S { return S { a:9, b:8/divisor }; }\n'
                      'fn main() { print("before"); target=make(); print("after"); }\n')
    count = 0
    for opt in (0, 2):
        prefix = out / f'fixed-result-failure-O{opt}'
        c, native, module = (prefix.with_suffix(ext) for ext in ('.c', '.native', '.wasm'))
        run([exe, f'-O{opt}', '--standalone', '-o', c, source])
        run([cc, c, '-pthread', '-lm', '-ldl', '-o', native])
        result = run([native], ok=False)
        assert result.returncode != 0 and result.stdout == b'before\n' and b'division by zero' in result.stderr
        run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, source])
        text = run([validator, 'print', module]).stdout.decode()
        text = text[:text.rfind(')')] + '  (export "test_stack_top_0" (global 0))\n)\n'
        wat = prefix.with_suffix('.wat'); wat.write_text(text)
        checked = out / f'fixed-result-failure-observed-O{opt}.wasm'
        run([validator, 'parse', wat, '-o', checked]); run([validator, 'validate', checked])
        result = run([node, ROOT / 'test/wasm_constructor_assignment_failure.mjs', checked])
        assert result.stdout == b'before\n' and not result.stderr
        count += 1
    return count


def check_target_failure(run, exe, cc, node, validator, out):
    source = out / 'fixed-result-target-bounds.goose'
    source.write_text('struct S { n:i64 }\n'
                      'var index:i64 = 1;\n'
                      'recursive fn make()->S { print("rhs"); return S { n:9 }; }\n'
                      'fn main() { var rows:S[]=[S { n:1 }]; print("before"); '
                      'rows[index]=make(); print("after"); }\n')
    count = 0
    for opt in (0, 2):
        prefix = out / f'fixed-result-target-bounds-O{opt}'
        c, native, module = (prefix.with_suffix(ext) for ext in ('.c', '.native', '.wasm'))
        run([exe, f'-O{opt}', '--standalone', '-o', c, source])
        run([cc, c, '-pthread', '-lm', '-ldl', '-o', native])
        result = run([native], ok=False)
        assert result.returncode != 0 and result.stdout == b'before\n'
        assert b'index 1 out of bounds (length 1)' in result.stderr
        run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, source])
        text = run([validator, 'print', module]).stdout.decode()
        text = text[:text.rfind(')')] + '  (export "test_stack_top_0" (global 0))\n)\n'
        wat = prefix.with_suffix('.wat'); wat.write_text(text)
        checked = out / f'fixed-result-target-bounds-observed-O{opt}.wasm'
        run([validator, 'parse', wat, '-o', checked]); run([validator, 'validate', checked])
        result = run([node, ROOT / 'test/wasm_constructor_assignment_failure.mjs', checked, 'bounds'])
        assert result.stdout == b'before\n' and not result.stderr
        count += 1
    return count


def check_nonlocal_guard(run, exe, cc, out):
    source = out / 'fixed-result-nonlocal-guard.goose'
    source.write_text('struct S{n:i64}\n'
                      'var calls:i64=0;\n'
                      'inline fn invoke<F>(a:S)->S{defer{calls++;}return F(a); }\n'
                      'recursive fn make(n:i64)->S{return invoke(S{n:n}){p=>'
                      'if p.n==7{return S{n:9};}S{n:p.n}};}\n'
                      'fn main(){var a:S=make(7);var b:S=make(3);assert(a.n==9);'
                      'assert(b.n==3);assert(calls==2);print("callback_exit");}\n')
    count = 0
    for opt in (0, 2):
        prefix = out / f'fixed-result-nonlocal-guard-O{opt}'
        c, native, module = (prefix.with_suffix(ext) for ext in ('.c', '.native', '.wasm'))
        run([exe, f'-O{opt}', '--standalone', '-o', c, source])
        run([cc, c, '-pthread', '-lm', '-ldl', '-o', native])
        reference = run([native]); assert reference.stdout == b'callback_exit\n' and not reference.stderr
        module.unlink(missing_ok=True)
        result = run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, source], ok=False)
        assert result.returncode == 1 and b'nonlocal return across a Wasm call requires the pending exception lowering' in result.stderr
        assert not module.exists()
        count += 1
    return count
