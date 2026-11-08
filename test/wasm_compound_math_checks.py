"""Arithmetic statement images, old-value capture, exits and native trap order."""
from pathlib import Path
import re
from wasm_data_iteration_checks import function_span
from wasm_fixed_binary_checks import emit
ROOT = Path(__file__).resolve().parents[1]


def check_images(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        for data in (False, True):
            name = 'data_owner' if data else 'owner'
            text = run([validator, 'print', out / f'wasm_compound_math_{name}-O{opt}.wasm']).stdout.decode()
            args = [node, ROOT / 'test/wasm_compound_math_owner.mjs']
            def observe(label, value, mode='finite', ok=True):
                module = emit(run, validator, out, f'compound-{name}-{label}-O{opt}', value, 2 if data else 1)
                return run(args + [module, 'data' if data else 'frame', mode], ok=ok)
            for mode in ('finite', 'bits', 'nan'):
                result = observe(mode, text, mode)
                expected = b'before\nafter=false,false\n' if mode == 'nan' else b'before\nafter=true,true\n'
                assert result.stdout == expected and not result.stderr
                count += 1
            a, z = function_span(text, 'main'); body = text[a:z]
            f32, n = re.subn(r'\bf32.add\b', 'f32.sub', body); assert n == 1
            f64, n = re.subn(r'\bf64.add\b', 'f64.sub', body); assert n == 1
            offset, n = re.subn(r'\bf64.store( 1)? offset=6\b', r'f64.store\1 offset=7', body); assert n == 1
            # The data element starts after its u32 row count; the frame
            # fixture's first global is at the checked non-null address 8.
            padding = ('i32.const 9\n      i32.const 0\n      i32.store8 1' if data else
                       'i32.const 12\n      i32.const 0\n      i32.store8')
            clobber, n = re.subn(r'(f64.store[^\n]*\n)', lambda m: m[1] + '      ' + padding + '\n', body)
            assert n == 1
            cases = [('wrong-f32', f32), ('wrong-f64', f64), ('wrong-offset', offset), ('padding', clobber)]
            if data:
                wrong_memory, n = re.subn(r'\bf32.store 1\b', 'f32.store', body); assert n == 1
                cases.append(('wrong-memory', wrong_memory))
            for label, modified in cases:
                result = observe(label, text[:a] + modified + text[z:], ok=False)
                reason = (b'compound data memory image differs' if data and label != 'wrong-memory'
                          else b'compound memory 0 image differs')
                assert result.returncode == 1 and reason in result.stderr, (label, result.stderr)
                count += 1
    return count


def check_snapshot(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        text = run([validator, 'print', out / f'wasm_compound_math_snapshot_owner-O{opt}.wasm']).stdout.decode()
        args = [node, ROOT / 'test/wasm_compound_math_snapshot.mjs']
        result = run(args + [emit(run, validator, out, f'compound-snapshot-healthy-O{opt}', text)])
        assert result.stdout == b'before\nright\nafter=10,-4,1\n' and not result.stderr
        count += 1
        a, z = function_span(text, 'main'); body = text[a:z]
        bases = re.findall(r'i32.const 16\n\s*call \$goose.reserve_frame\n\s*local.set (\d+)', body)
        assert len(bases) == 2
        loads = list(re.finditer(rf'local.get {bases[0]}\n\s*i64.extend_i32_u', body)); assert len(loads) == 2
        source = re.findall(r'i32.const 8\n\s*local.set (\d+)', body); assert source
        m = loads[-1]
        modified = body[:m.start()] + re.sub(r'local.get \d+', f'local.get {source[0]}', m[0], count=1) + body[m.end():]
        result = run(args + [emit(run, validator, out, f'compound-snapshot-wrong-source-O{opt}',
                                 text[:a] + modified + text[z:])], ok=False)
        assert result.returncode == 1 and b'compound snapshot result image differs' in result.stderr
        count += 1
    return count


def check_loops(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        for discard in (False, True):
            name = 'wasm_negation_discard_loop' if discard else 'wasm_compound_math_early_continue'
            text = run([validator, 'print', out / f'{name}-O{opt}.wasm']).stdout.decode()
            args = [node, ROOT / 'test/wasm_compound_math_loop.mjs']
            mode = ['discard'] if discard else []
            result = run(args + [emit(run, validator, out, f'{name}-healthy-O{opt}', text)] + mode)
            expected = b'head\n' * 4 + (b'negation_loop\n' if discard else b'early_continue\n')
            assert result.stdout == expected and not result.stderr
            count += 1
            a, z = function_span(text, 'main'); body = text[a:z]
            restores = list(re.finditer(r'(?m)^\s*global.set 0\s*$', body)); assert len(restores) >= 2
            restore = restores[-1] if discard else restores[0]
            modified = body[:restore.start()] + '\n      drop\n' + body[restore.end():]
            result = run(args + [emit(run, validator, out, f'{name}-missing-restore-O{opt}',
                                     text[:a] + modified + text[z:])] + mode, ok=False)
            assert result.returncode == 1 and b'arithmetic statement live frame top differs' in result.stderr
            count += 1
    return count


def check_global(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        text = run([validator, 'print', out / f'wasm_compound_math_index_effect-O{opt}.wasm']).stdout.decode()
        args = [node, ROOT / 'test/wasm_compound_math_global.mjs']
        result = run(args + [emit(run, validator, out, f'compound-global-healthy-O{opt}', text, 2)])
        assert result.stdout == b'index_effect\n' and not result.stderr
        count += 1
        a, z = function_span(text, 'main'); body = text[a:z]
        end = body.rfind(')'); assert end >= 0
        modified = body[:end] + '    global.get 1\n    i32.const 1\n    i32.add\n    global.set 1\n  ' + body[end:]
        result = run(args + [emit(run, validator, out, f'compound-global-wrong-top-O{opt}',
                                 text[:a] + modified + text[z:], 2)], ok=False)
        assert result.returncode == 1 and b'compound global data top differs' in result.stderr
        count += 1
    return count


def check_failures(run, exe, cc, node, validator, out):
    count = 0
    for name, lhs, rhs, op, first, second, reason in [
        ('division', '[8,9]', '[2,0]', '/=', 4, 9, b'division by zero'),
        ('modulo', '[8,9]', '[3,0]', '%=', 2, 9, b'division by zero'),
        ('overflow', '[8,-9223372036854775808]', '[2,-1]', '/=', 4, -9223372036854775808,
         b'integer overflow in division'),
    ]:
        path = out / f'compound-failure-{name}.goose'
        path.write_text(f'var target:i64[2]={lhs};var divisor:i64[2]={rhs};\n'
                        f'fn main(){{print("before");target{op}divisor;print("after");}}\n')
        for opt in (0, 2):
            prefix = out / f'compound-failure-{name}-O{opt}'
            c, native, module = (prefix.with_suffix(ext) for ext in ('.c', '.native', '.wasm'))
            run([exe, f'-O{opt}', '--standalone', '-o', c, path])
            original = c.read_text(); assert original.count('a2_i64 target_g;') == 1
            hooked, n = re.subn(r'(static GS_NORETURN void gs_fail\([^\n]+\) \{)',
                               'static void test_compound_state(void);\n\\1\n    test_compound_state();', original)
            assert n == 1
            hooked += ('\nstatic void test_compound_state(void) {\n'
                       '    fprintf(stderr, "compound-state=%lld,%lld\\n", '
                       '(long long)GS_GL->target_g.e[0], (long long)GS_GL->target_g.e[1]);\n}\n')
            instrumented = out / f'{prefix.name}-observed.c'; instrumented.write_text(hooked)
            run([cc, f'-O{opt}', instrumented, '-pthread', '-lm', '-ldl', '-o', native])
            result = run([native], ok=False)
            assert result.returncode != 0 and result.stdout == b'before\n' and reason in result.stderr
            assert result.stderr.startswith(f'compound-state={first},{second}\n'.encode()), result.stderr
            run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, path])
            text = run([validator, 'print', module]).stdout.decode()
            args = [node, ROOT / 'test/wasm_compound_math_failure.mjs']
            result = run(args + [emit(run, validator, out, prefix.name + '-observed', text), name])
            assert result.stdout == b'before\n' and not result.stderr
            count += 1
            a, z = function_span(text, 'main'); body = text[a:z]
            modified, n = re.subn(r'(?m)^\s*i64.store align=1\s*$', '\n          drop\n          drop\n', body)
            assert n == 1
            result = run(args + [emit(run, validator, out, prefix.name + '-missing-store',
                                     text[:a] + modified + text[z:]), name], ok=False)
            assert result.returncode == 1 and b'compound partial-write memory image differs' in result.stderr
            count += 1
    return count
