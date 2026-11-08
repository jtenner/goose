"""Zero-payload call results retain distinct complete owners and cleanup."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def check_completed(run, exe, source, module, opt, expected, node, validator, wasmtime_python):
    run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, source])
    run([validator, 'validate', module])
    result = run([node, ROOT / 'test/wasm_multimemory.mjs', module, '0', 'no-data'])
    assert result.stdout == expected and not result.stderr
    if wasmtime_python:
        result = run([wasmtime_python, ROOT / 'test/wasmtime_host.py', module])
        assert result.stdout == expected and not result.stderr


def check_images(run, node, validator, out):
    import re
    from wasm_data_iteration_checks import function_span
    from wasm_fixed_binary_checks import emit
    count = 0
    for opt in (0, 2):
        for name in ('owner', 'enum_owner'):
            text = run([validator, 'print', out / f'wasm_zero_call_{name}-O{opt}.wasm']).stdout.decode()
            args = [node, ROOT / 'test/wasm_zero_call_owner.mjs']
            result = run(args + [emit(run, validator, out, f'zero-call-{name}-healthy-O{opt}', text)])
            assert result.stdout == b'before\ninside\nafter\n' and not result.stderr
            count += 1
            a, z = function_span(text, 'same'); body = text[a:z]
            offset, n = re.subn(r'\bi32.store8\b', 'i32.store8 offset=3', body); assert n == 1
            reservation, n = re.subn(r'i32.const 1(?=\n\s*call \$goose.reserve_frame)', 'i32.const 0', body)
            assert n == 1
            for label, modified, reason in [
                ('wrong-offset', offset, b'zero call memory 0 image differs'),
                ('missing-reservation', reservation, b'zero call live owner top differs'),
            ]:
                result = run(args + [emit(run, validator, out, f'zero-call-{name}-{label}-O{opt}',
                                         text[:a] + modified + text[z:])], ok=False)
                assert result.returncode == 1 and reason in result.stderr, (label, result.stderr)
                count += 1
    return count


def check_loop(run, node, validator, out):
    import re
    from wasm_data_iteration_checks import function_span
    from wasm_fixed_binary_checks import emit
    count = 0
    for opt in (0, 2):
        text = run([validator, 'print', out / f'wasm_zero_call_loop-O{opt}.wasm']).stdout.decode()
        args = [node, ROOT / 'test/wasm_zero_call_loop.mjs']
        result = run(args + [emit(run, validator, out, f'zero-call-loop-healthy-O{opt}', text)])
        assert result.stdout == b'head\n'*4 + b'loop\n' and not result.stderr
        count += 1
        a, z = function_span(text, 'main'); body = text[a:z]
        restores = list(re.finditer(r'(?m)^\s*global.set 0\s*$', body)); assert len(restores) >= 3
        restore = restores[-2]
        modified = body[:restore.start()] + '\n      drop\n' + body[restore.end():]
        result = run(args + [emit(run, validator, out, f'zero-call-loop-missing-restore-O{opt}',
                                 text[:a] + modified + text[z:])], ok=False)
        assert result.returncode == 1 and b'zero call loop live owner top differs' in result.stderr
        count += 1
    return count


def check_shared(run, node, validator, out):
    from wasm_data_iteration_checks import function_span
    from wasm_fixed_binary_checks import emit
    count = 0
    for opt in (0, 2):
        text = run([validator, 'print', out / f'wasm_zero_call_shared_data-O{opt}.wasm']).stdout.decode()
        args = [node, ROOT / 'test/wasm_zero_call_shared.mjs']
        result = run(args + [emit(run, validator, out, f'zero-call-shared-healthy-O{opt}', text, 2)])
        assert result.stdout == b'shared_data\n' and not result.stderr
        count += 1
        a, z = function_span(text, 'main'); body = text[a:z]; end = body.rfind(')'); assert end >= 0
        modified = body[:end] + '    global.get 1\n    i32.const 1\n    i32.add\n    global.set 1\n  ' + body[end:]
        result = run(args + [emit(run, validator, out, f'zero-call-shared-wrong-top-O{opt}',
                                 text[:a] + modified + text[z:], 2)], ok=False)
        assert result.returncode == 1 and b'zero call global data top differs' in result.stderr
        count += 1
    return count


def check_rejections(run, exe, out):
    cases = [
        ('array-field', 'struct H{tag:u8,empty:i64[0]}fn main(){}\n', b'field empty of struct H cannot be a zero-length array'),
        ('array-middle-field', 'struct H{left:i64,empty:i64[0],right:i64}fn main(){}\n', b'field empty of struct H cannot be a zero-length array'),
        ('variant-field', 'enum E{Empty,Value{n:i64}}struct H{tag:u8,empty:E.Empty}fn main(){}\n', b'field empty of struct H cannot be a variant type with no fields'),
        ('variant-middle-field', 'enum E{Empty,Value{n:i64}}struct H{left:i64,empty:E.Empty,right:i64}fn main(){}\n', b'field empty of struct H cannot be a variant type with no fields'),
        ('array-element', 'fn main(){var x:i64[0][2]=[[],[]];print(x.len);}\n', b'an element cannot be a zero-length array'),
        ('variant-element', 'enum E{Empty,Value{n:i64}}fn main(){var x:E.Empty[2]=[default<E.Empty>();2];print(x.len);}\n', b'an element cannot be a variant type with no fields'),
    ]
    count = 0
    for name, source, reason in cases:
        path = out / f'zero-call-rejection-{name}.goose'; path.write_text(source)
        for opt in (0, 2):
            for target in ('native', 'wasm'):
                file = out / f'zero-call-rejection-{name}-O{opt}.{ "c" if target == "native" else "wasm" }'
                file.unlink(missing_ok=True)
                args = [exe, f'-O{opt}'] + (['--standalone'] if target == 'native' else ['--target', 'wasm'])
                result = run(args + ['-o', file, path], ok=False)
                assert result.returncode == 1 and reason in result.stderr and not file.exists(), (name, result.stderr)
            count += 1
    return count
