"""Fixed-source assignment payloads, retained capacity, empty calls and count widths."""
from pathlib import Path
import re
from wasm_data_iteration_checks import function_span
from wasm_fixed_binary_checks import emit
ROOT = Path(__file__).resolve().parents[1]


def copy_size(body, old, new):
    result, n = re.subn(rf'i32.const {old}(?=\n\s*memory.copy\b)', f'i32.const {new}', body)
    assert n == 1
    return result


def after_copy(body, count):
    index = body.index('memory.copy')
    result, n = re.subn(r'i64.const \d+(?=\n\s*i64.store8\b)', f'i64.const {count}', body[index:], count=1)
    assert n == 1
    return body[:index] + result


def check_owners(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        for mode in ('stored', 'call', 'zero'):
            text = run([validator, 'print', out / f'wasm_fixed_array_assignment_layout_owner_{mode}-O{opt}.wasm']).stdout.decode()
            args = [node, ROOT / 'test/wasm_fixed_array_assignment_owner.mjs']
            def observed(label, value, ok=True):
                return run(args + [emit(run, validator, out, f'fixed-assignment-{mode}-{label}-O{opt}', value), mode], ok=ok)
            expected = b'before\ninside\nafter\n' if mode == 'zero' else b'before\nafter\n'
            result = observed('healthy', text); assert result.stdout == expected and not result.stderr
            count += 1
            a, z = function_span(text, 'main'); body = text[a:z]
            if mode == 'zero':
                reserve, n = re.subn(r'i32.const 1(?=\n\s*call \$goose.reserve_frame)', 'i32.const 0', body); assert n == 1
                controls = [
                    ('long', copy_size(body, 0, 2), b'array assignment memory 0 image differs'),
                    ('count', after_copy(body, 1), b'array assignment memory 0 image differs'),
                    ('reserve', reserve, b'array assignment live frame top differs'),
                ]
            else:
                restore, n = re.subn(r'global.set 0\b', 'drop', body, count=1); assert n == 1
                controls = [
                    ('short', copy_size(body, 16, 8), b'array assignment memory 0 image differs'),
                    ('long', copy_size(body, 16, 24), b'array assignment memory 0 image differs'),
                    ('count', after_copy(body, 3), b'array assignment memory 0 image differs'),
                    ('restore', restore, b'array assignment live frame top differs' if mode == 'call'
                     else b'array assignment completed frame top differs'),
                ]
            for label, modified, reason in controls:
                result = observed(label, text[:a] + modified + text[z:], False)
                assert result.returncode == 1 and reason in result.stderr, (mode, label, result.stderr)
                count += 1
    return count


def check_data(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        text = run([validator, 'print', out / f'wasm_fixed_array_assignment_layout_owner_data-O{opt}.wasm']).stdout.decode()
        args = [node, ROOT / 'test/wasm_fixed_array_assignment_data.mjs']
        def observed(label, value, ok=True):
            return run(args + [emit(run, validator, out, f'fixed-assignment-data-{label}-O{opt}', value, 2)], ok=ok)
        result = observed('healthy', text); assert result.stdout == b'before\nafter\n' and not result.stderr
        count += 1
        a, z = function_span(text, 'main'); body = text[a:z]; index = body.index('memory.copy')
        tail, n = re.subn(r'i64.const 2\b', 'i64.const 3', body[index:], count=1); assert n == 1
        wrong_count = body[:index] + tail
        release, n = re.subn(r'memory.copy 1 0\b', 'memory.copy 1 0\n      i32.const 1\n      global.set 1', body); assert n == 1
        memory, n = re.subn(r'memory.copy 1 0\b', 'memory.copy', body); assert n == 1
        for label, modified, reason in [
            ('short', copy_size(body, 16, 8), b'data array assignment data image differs'),
            ('long', copy_size(body, 16, 24), b'data array assignment data image differs'),
            ('count', wrong_count, b'data array assignment data image differs'),
            ('release', release, b'data array assignment live data top differs'),
            ('memory', memory, b'data array assignment memory 0 image differs'),
        ]:
            result = observed(label, text[:a] + modified + text[z:], False)
            assert result.returncode == 1 and reason in result.stderr, (label, result.stderr)
            count += 1
    return count


def check_wide(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        text = run([validator, 'print', out / f'wasm_fixed_array_assignment_layout_owner_wide-O{opt}.wasm']).stdout.decode()
        args = [node, ROOT / 'test/wasm_fixed_array_assignment_wide.mjs']
        def observed(label, value, ok=True):
            return run(args + [emit(run, validator, out, f'fixed-assignment-wide-{label}-O{opt}', value)], ok=ok)
        result = observed('healthy', text); assert result.stdout == b'before\nwide\nafter\n' and not result.stderr
        count += 1
        a, z = function_span(text, 'main'); body = text[a:z]
        width, n = re.subn(r'(i64.const 2\n\s*)i64.store16\b', r'\1i64.store8', body); assert n == 1
        restore, n = re.subn(r'global.set 0\b', 'drop', body, count=1); assert n == 1
        for label, modified, reason in [
            ('short-big', copy_size(body, 256, 255), b'wide array assignment memory 0 image differs'),
            ('long-big', copy_size(body, 256, 257), b'wide array assignment memory 0 image differs'),
            ('short-small', copy_size(body, 2, 1), b'wide array assignment memory 0 image differs'),
            ('long-small', copy_size(body, 2, 3), b'wide array assignment memory 0 image differs'),
            ('width', width, b'wide array assignment memory 0 image differs'),
            ('restore', restore, b'wide array assignment completed frame top differs'),
        ]:
            result = observed(label, text[:a] + modified + text[z:], False)
            assert result.returncode == 1 and reason in result.stderr, (label, result.stderr)
            count += 1
    return count


def check_failures(run, exe, cc, node, validator, wasmtime_python, out):
    import json
    count = 0
    cases = [
        ('division', 'var divisor:i64=0;var target:i64[..3]=[1,2,3];\n'
         'recursive fn make()->i64[2]{return[99,7/divisor];}\n'
         'fn main(){print("before");target=make();print("after");}\n', b'division by zero'),
        ('bounds', 'struct H{values:i64[..3]}var index:i64=1;\n'
         'recursive fn make()->i64[2]{print("rhs");return[7,-8];}\n'
         'fn main(){var rows:H[]=[H{[1,2,3]}];print("before");rows[index].values=make();print("after");}\n',
         b'index 1 out of bounds (length 1)'),
    ]
    for name, source, reason in cases:
        path = out / f'fixed-array-assignment-failure-{name}.goose'; path.write_text(source)
        for opt in (0, 2):
            prefix = out / f'fixed-array-assignment-failure-{name}-O{opt}'
            c, native, module = (prefix.with_suffix(ext) for ext in ('.c', '.native', '.wasm'))
            run([exe, f'-O{opt}', '--standalone', '-o', c, path])
            compiled = c
            if name == 'division':
                original = c.read_text(); assert original.count('l3_i64 target_g;') == 1
                hooked, n = re.subn(r'(static GS_NORETURN void gs_fail\([^\n]+\) \{)',
                                   'static void test_assignment_state(void);\n\\1\n    test_assignment_state();', original)
                assert n == 1
                hooked += ('\nstatic void test_assignment_state(void) {\n'
                           '    fprintf(stderr, "assignment-state=%lld,%lld,%lld,%lld\\n", '
                           '(long long)GS_GL->target_g.len, (long long)GS_GL->target_g.e[0], '
                           '(long long)GS_GL->target_g.e[1], (long long)GS_GL->target_g.e[2]);\n}\n')
                compiled = out / f'{prefix.name}-observed.c'; compiled.write_text(hooked)
            run([cc, f'-O{opt}', compiled, '-pthread', '-lm', '-ldl', '-o', native])
            result = run([native], ok=False)
            assert result.returncode != 0 and result.stdout == b'before\n' and reason in result.stderr, result.stderr
            if name == 'division': assert result.stderr.startswith(b'assignment-state=3,1,2,3\n'), result.stderr
            run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, path])
            text = run([validator, 'print', module]).stdout.decode()
            args = [node, ROOT / 'test/wasm_fixed_array_assignment_failure.mjs']
            metadata = out / f'{prefix.name}-state.json'
            result = run(args + [emit(run, validator, out, prefix.name + '-healthy', text, 2 if name == 'bounds' else 1), name, metadata])
            assert result.stdout == b'before\n' and not result.stderr
            if wasmtime_python:
                result = run([wasmtime_python, ROOT / 'test/wasmtime_host.py', module], ok=False)
                wasm_reason = b'array index out of bounds' if name == 'bounds' else b'division by zero'
                assert result.returncode == 1 and result.stdout == b'before\n' and wasm_reason in result.stderr
            count += 1
            a, z = function_span(text, 'main'); body = text[a:z]
            if name == 'division':
                target = json.loads(metadata.read_text())['target']
                modified, n = re.subn(r'local.get \d+(?=\n\s*call \$make\.\d+\b)', f'i32.const {target}', body)
                assert n == 1
                error = b'array assignment protected memory 0 image differs'
            else:
                guards = list(re.finditer(r'\bi64.ge_u\b', body)); assert guards
                last = guards[-1]; modified = body[:last.start()] + 'i64.lt_u' + body[last.end():]
                error = b'array assignment invalid target ran RHS'
            result = run(args + [emit(run, validator, out, prefix.name + '-damaged',
                                     text[:a] + modified + text[z:], 2 if name == 'bounds' else 1), name], ok=False)
            assert result.returncode == 1 and error in result.stderr, (name, result.stderr)
            count += 1
    return count
