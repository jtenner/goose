"""Exact FP payloads, padding, memory namespaces and live temporary cleanup."""
from pathlib import Path
import re
from wasm_data_iteration_checks import function_span
ROOT = Path(__file__).resolve().parents[1]


def check_images(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        for data in (False, True):
            name = 'data_owner' if data else 'owner'
            module = out / f'wasm_fixed_negation_{name}-O{opt}.wasm'
            text = run([validator, 'print', module]).stdout.decode()
            def emit(label, value):
                wat = out / f'fixed-negation-{name}-{label}-O{opt}.wat'; wasm = wat.with_suffix('.wasm')
                exports = ''.join(f'  (export "test_stack_top_{i}" (global {i}))\n' for i in range(2 if data else 1))
                wat.write_text(value[:value.rfind(')')] + exports + ')\n')
                run([validator, 'parse', wat, '-o', wasm]); run([validator, 'validate', wasm])
                return wasm
            args = [node, ROOT / 'test/wasm_fixed_negation_owner.mjs']
            result = run(args + [emit('healthy', text), 'data' if data else 'frame'])
            assert result.stdout == b'before\nafter=false,false\n' and not result.stderr
            count += 1
            a, z = function_span(text, 'main'); body = text[a:z]
            missing, n = re.subn(r'(?m)^\s*f32.neg\s*$', '', body); assert n == 1
            wrong_op, n = re.subn(r'\bf64.neg\b', 'f64.abs', body); assert n == 1
            offset = 10 if data else 6  # Data element follows the u32 count prefix.
            wrong_offset, n = re.subn(rf'\bf64.store( 1)? offset={offset}\b',
                                      rf'f64.store\1 offset={offset + 1}', body); assert n == 1
            cases = [('missing-negation', missing), ('wrong-op', wrong_op), ('wrong-offset', wrong_offset)]
            if data:
                wrong_memory, n = re.subn(r'\bf32.store 1\b', 'f32.store', body); assert n == 1
                cases.append(('wrong-memory', wrong_memory))
            for label, modified in cases:
                damaged = emit(label, text[:a] + modified + text[z:])
                result = run(args + [damaged, 'data' if data else 'frame'], ok=False)
                reason = (b'fixed negation data memory image differs' if data and label != 'wrong-memory' else
                          b'fixed negation memory 0 image differs')
                assert result.returncode == 1 and reason in result.stderr, (label, result.stderr)
                count += 1
    return count


def check_loop(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        module = out / f'wasm_fixed_negation_loop_exit-O{opt}.wasm'
        text = run([validator, 'print', module]).stdout.decode()
        def emit(name, value):
            wat = out / f'fixed-negation-loop-{name}-O{opt}.wat'; wasm = wat.with_suffix('.wasm')
            wat.write_text(value[:value.rfind(')')] + '  (export "test_stack_top_0" (global 0))\n)\n')
            run([validator, 'parse', wat, '-o', wasm]); run([validator, 'validate', wasm])
            return wasm
        result = run([node, ROOT / 'test/wasm_fixed_negation_loop.mjs', emit('healthy', text)])
        assert result.stdout == b'head\nhead\nhead\nhead\nloop_exit\n' and not result.stderr
        count += 1
        a, z = function_span(text, 'main'); body = text[a:z]
        restores = list(re.finditer(r'(?m)^\s*global.set 0\s*$', body)); assert len(restores) >= 4
        restore = restores[0]
        modified = body[:restore.start()] + '\n      drop\n' + body[restore.end():]
        result = run([node, ROOT / 'test/wasm_fixed_negation_loop.mjs',
                      emit('missing-continue-restore', text[:a] + modified + text[z:])], ok=False)
        assert result.returncode == 1 and b'fixed negation loop live frame top differs' in result.stderr
        count += 1
    return count
