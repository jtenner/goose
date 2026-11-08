"""Runtime-sized construction from fixed-storage limited arrays."""
from pathlib import Path
import re
from wasm_data_iteration_checks import function_span
from wasm_fixed_binary_checks import emit
ROOT = Path(__file__).resolve().parents[1]


def replace_one(body, pattern, value):
    result, count = re.subn(pattern, value, body, count=1)
    assert count == 1, pattern
    return result


def check_images(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        for mode, case, short, long in [('padded', 'padded', 14, 42), ('varint', 'owner_varint', 127, 129)]:
            text = run([validator, 'print', out / f'wasm_limited_array_conversion_{case}-O{opt}.wasm']).stdout.decode()
            args = [node, ROOT / 'test/wasm_limited_array_conversion_owner.mjs']
            def observed(label, value, ok=True):
                return run(args + [emit(run, validator, out, f'limited-conversion-{case}-{label}-O{opt}', value, 2), mode], ok=ok)
            result = observed('healthy', text); assert result.stdout == b'before\nafter\n' and not result.stderr
            count += 1
            a, z = function_span(text, 'main'); body = text[a:z]
            copy_arg = r'local.get \d+(?=\n\s*memory.copy 1 0\b)'
            controls = [
                ('short', replace_one(body, copy_arg, f'i32.const {short}'), b'limited receiver data image differs'),
                ('long', replace_one(body, copy_arg, f'i32.const {long}'), b'limited receiver data image differs'),
                ('frame', replace_one(body, r'global.set 0\b', 'drop'), b'limited receiver completed frame top differs'),
                ('data', replace_one(body, r'global.set 1\b', 'drop'), b'limited receiver completed data top differs'),
            ]
            if mode == 'padded':
                controls += [
                    ('width', replace_one(body, r'i64.store32 1\b', 'i64.store16 1'), b'limited receiver data image differs'),
                    ('memory', replace_one(body, r'memory.copy 1 0\b', 'memory.copy'), b'limited receiver memory 0 image differs'),
                ]
            else:
                controls += [
                    ('continuation', replace_one(body, r'i64.const 128(?=\n\s*i64.or)', 'i64.const 0'), b'limited receiver data image differs'),
                    ('prefix-bytes', replace_one(body, r'i64.const 128(?=\n\s*i64.lt_u)', 'i64.const 256'), b'limited receiver live data top differs'),
                ]
            for label, modified, reason in controls:
                result = observed(label, text[:a] + modified + text[z:], False)
                assert result.returncode == 1 and reason in result.stderr, (case, label, result.stderr)
                count += 1
    return count


def check_zero(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        for mode in ('variable', 'runtime'):
            text = run([validator, 'print', out / f'wasm_limited_array_conversion_zero_call_{mode}-O{opt}.wasm']).stdout.decode()
            args = [node, ROOT / 'test/wasm_limited_array_conversion_zero.mjs']
            def observed(label, value, ok=True):
                return run(args + [emit(run, validator, out, f'limited-conversion-zero-{mode}-{label}-O{opt}', value, 2), mode], ok=ok)
            result = observed('healthy', text); assert result.stdout == ('inside\nzero_call_' + mode + '\n').encode() and not result.stderr
            count += 1
            a, z = function_span(text, 'main'); body = text[a:z]
            controls = [
                ('long', replace_one(body, r'local.get \d+(?=\n\s*memory.copy 1 0\b)', 'i32.const 1'), b'empty limited receiver data image differs'),
                ('early', replace_one(body, r'memory.copy 1 0\b', 'memory.copy 1 0\n      i32.const 1\n      global.set 1'), b'empty limited receiver was released early'),
                ('reserve', replace_one(body, r'i32.const 1(?=\n\s*call \$goose.reserve_frame)', 'i32.const 0'), b'empty limited source live frame top differs'),
                ('temporary', replace_one(body, r'global.set 0\b', 'drop'), b'empty limited source temporary was not released'),
                ('data', replace_one(body, r'global.set 1\b', 'drop'), b'empty limited completed data top differs'),
            ]
            for label, modified, reason in controls:
                result = observed(label, text[:a] + modified + text[z:], False)
                assert result.returncode == 1 and reason in result.stderr, (mode, label, result.stderr)
                count += 1
    return count


def check_failures(run, exe, cc, node, validator, wasmtime_python, out):
    count = 0
    for amount, storage in [(256, 'u8'), (65536, 'u16')]:
        source = (f'fn main(){{var a:u8[..{amount}]=[];for i in 0..{amount}{{a.push(i as u8);}}'
                  f'print("before");var b:u8[{storage}]=a;print("after");}}\n')
        path = out / f'limited-conversion-failure-{storage}.goose'; path.write_text(source)
        for opt in (0, 2):
            prefix = out / f'limited-conversion-failure-{storage}-O{opt}'
            c, native, module = (prefix.with_suffix(ext) for ext in ('.c', '.native', '.wasm'))
            run([exe, f'-O{opt}', '--standalone', '-o', c, path]); run([cc, f'-O{opt}', c, '-pthread', '-lm', '-ldl', '-o', native])
            result = run([native], ok=False)
            assert result.returncode != 0 and result.stdout == b'before\n' and b'array length exceeds storage range' in result.stderr, result.stderr
            run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, path])
            text = run([validator, 'print', module]).stdout.decode()
            args = [node, ROOT / 'test/wasm_limited_array_conversion_failure.mjs']
            result = run(args + [emit(run, validator, out, prefix.name + '-healthy', text, 2), amount]); assert result.stdout == b'before\n' and not result.stderr
            if wasmtime_python:
                result = run([wasmtime_python, ROOT / 'test/wasmtime_host.py', module], ok=False)
                assert result.returncode == 1 and result.stdout == b'before\n' and b'goose runtime error: array length exceeds stored prefix at ' in result.stderr
            count += 1
            a, z = function_span(text, 'main'); body = text[a:z]
            modified = replace_one(body, rf'i64.const {amount - 1}\n(\s*)i64.gt_u', rf'i64.const {amount - 1}\n\1i64.lt_u')
            result = run(args + [emit(run, validator, out, prefix.name + '-guard', text[:a] + modified + text[z:], 2), amount], ok=False)
            assert result.returncode == 1 and b'prefix range executed after failed conversion' in result.stderr, result.stderr
            count += 1
    return count
