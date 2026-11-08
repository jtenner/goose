"""Fixed binary arithmetic images, ordered snapshots, cleanup and trap atomicity."""
from pathlib import Path
import re
from wasm_data_iteration_checks import function_span
ROOT = Path(__file__).resolve().parents[1]


def emit(run, validator, out, name, text, globals=1):
    wat = out / (name + '.wat'); module = wat.with_suffix('.wasm')
    exports = ''.join(f'  (export "test_stack_top_{i}" (global {i}))\n' for i in range(globals))
    wat.write_text(text[:text.rfind(')')] + exports + ')\n')
    run([validator, 'parse', wat, '-o', module]); run([validator, 'validate', module])
    return module


def check_images(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        for data in (False, True):
            name = 'data_owner' if data else 'owner'
            text = run([validator, 'print', out / f'wasm_fixed_binary_{name}-O{opt}.wasm']).stdout.decode()
            args = [node, ROOT / 'test/wasm_fixed_binary_owner.mjs']
            def observe(label, value, mode='finite', ok=True):
                module = emit(run, validator, out, f'fixed-binary-{name}-{label}-O{opt}', value, 2 if data else 1)
                return run(args + [module, 'data' if data else 'frame', mode], ok=ok)
            for mode in ('finite', 'bits', 'nan'):
                result = observe(mode, text, mode)
                expected = b'before\nafter=false,false\n' if mode == 'nan' else b'before\nafter=true,true\n'
                assert result.stdout == expected and not result.stderr
                count += 1
            a, z = function_span(text, 'main'); body = text[a:z]
            f32, n = re.subn(r'\bf32\.add\b', 'f32.sub', body); assert n == 1
            f64, n = re.subn(r'\bf64\.add\b', 'f64.sub', body); assert n == 1
            offset = 10 if data else 6
            wrong_offset, n = re.subn(rf'\bf64\.store( 1)? offset={offset}\b',
                                      rf'f64.store\1 offset={offset + 1}', body); assert n == 1
            if data:
                padding = 'i32.const 9\n      i32.const 0\n      i32.store8 1'
            else:
                bases = re.findall(r'i32\.const 14\n\s*call \$goose.reserve_frame\n\s*local.set (\d+)', body)
                assert len(bases) == 1
                padding = f'local.get {bases[0]}\n      i32.const 0\n      i32.store8 offset=4'
            clobber, n = re.subn(r'(f64\.store[^\n]*\n)', lambda m: m[1] + '      ' + padding + '\n', body)
            assert n == 1
            cases = [('wrong-f32', f32), ('wrong-f64', f64), ('wrong-offset', wrong_offset), ('padding', clobber)]
            if data:
                wrong_memory, n = re.subn(r'\bf32\.store 1\b', 'f32.store', body); assert n == 1
                cases.append(('wrong-memory', wrong_memory))
            for label, modified in cases:
                result = observe(label, text[:a] + modified + text[z:], ok=False)
                reason = (b'fixed binary data memory image differs' if data and label != 'wrong-memory'
                          else b'fixed binary memory 0 image differs')
                assert result.returncode == 1 and reason in result.stderr, (label, result.stderr)
                count += 1
    return count


def check_snapshot(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        text = run([validator, 'print', out / f'wasm_fixed_binary_snapshot_owner-O{opt}.wasm']).stdout.decode()
        args = [node, ROOT / 'test/wasm_fixed_binary_snapshot.mjs']
        result = run(args + [emit(run, validator, out, f'fixed-binary-snapshot-healthy-O{opt}', text)])
        assert result.stdout == b'before\nright\nafter=10,-4,1\n' and not result.stderr
        count += 1
        a, z = function_span(text, 'source_value'); getter = text[a:z]
        source = re.findall(r'i32.const (\d+)\n\s*local.set \d+\n\s*br 0', getter)
        assert len(source) == 1
        a, z = function_span(text, 'main'); body = text[a:z]
        bases = re.findall(r'i32.const 16\n\s*call \$goose.reserve_frame\n\s*local.set (\d+)', body)
        assert len(bases) == 3
        loads = list(re.finditer(rf'local.get {bases[1]}\n\s*i64.extend_i32_u', body)); assert len(loads) == 2
        m = loads[-1]
        modified = body[:m.start()] + re.sub(r'local.get \d+', f'i32.const {source[0]}', m[0], count=1) + body[m.end():]
        result = run(args + [emit(run, validator, out, f'fixed-binary-snapshot-wrong-source-O{opt}',
                                 text[:a] + modified + text[z:])], ok=False)
        assert result.returncode == 1 and b'fixed binary snapshot result image differs' in result.stderr
        count += 1
    return count


def check_loop(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        text = run([validator, 'print', out / f'wasm_fixed_binary_early_continue-O{opt}.wasm']).stdout.decode()
        args = [node, ROOT / 'test/wasm_fixed_binary_loop.mjs']
        result = run(args + [emit(run, validator, out, f'fixed-binary-loop-healthy-O{opt}', text)])
        assert result.stdout == b'head\nhead\nhead\nhead\nearly_continue\n' and not result.stderr
        count += 1
        a, z = function_span(text, 'main'); body = text[a:z]
        modified, n = re.subn(r'(?m)^\s*global.set 0\s*$', '\n      drop\n', body, count=1); assert n == 1
        result = run(args + [emit(run, validator, out, f'fixed-binary-loop-missing-restore-O{opt}',
                                 text[:a] + modified + text[z:])], ok=False)
        assert result.returncode == 1 and b'fixed binary loop live frame top differs' in result.stderr
        count += 1
    return count


def check_failures(run, exe, cc, node, validator, out):
    count = 0
    for name, lhs, rhs, op, reason in [
        ('division', '[8,9]', '[2,0]', '/', b'division by zero'),
        ('modulo', '[8,9]', '[3,0]', '%', b'division by zero'),
        ('overflow', '[8,-9223372036854775808]', '[2,-1]', '/', b'integer overflow in division'),
    ]:
        path = out / f'fixed-binary-failure-{name}.goose'
        path.write_text(f'var target:i64[2]={lhs};var divisor:i64[2]={rhs};\n'
                        f'fn main(){{print("before");target=target{op}divisor;print("after");}}\n')
        for opt in (0, 2):
            prefix = out / f'fixed-binary-failure-{name}-O{opt}'
            c, native, module = (prefix.with_suffix(ext) for ext in ('.c', '.native', '.wasm'))
            run([exe, f'-O{opt}', '--standalone', '-o', c, path])
            run([cc, c, '-pthread', '-lm', '-ldl', '-o', native])
            result = run([native], ok=False)
            assert result.returncode != 0 and result.stdout == b'before\n' and reason in result.stderr, result.stderr
            run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, path])
            text = run([validator, 'print', module]).stdout.decode()
            observed = emit(run, validator, out, prefix.name + '-observed', text)
            result = run([node, ROOT / 'test/wasm_fixed_binary_failure.mjs', observed, name])
            assert result.stdout == b'before\n' and not result.stderr
            count += 1
    return count
