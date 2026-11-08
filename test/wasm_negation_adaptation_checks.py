"""Complete fresh images for fixed-to-limited negation and live source cleanup."""
from pathlib import Path
import re
from wasm_data_iteration_checks import function_span
ROOT = Path(__file__).resolve().parents[1]
HEADER = (r'(?P<op>i64\.const )2(?P<tail>(?:\n\s*(?:local\.(?:get|set) [^\n]+'
          r'|i32\.wrap_i64))*\n\s*i64\.store(?:8|16|32)\b)')


def check_images(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        for data in (False, True):
            name = 'data_owner' if data else 'owner'
            module = out / f'wasm_fixed_negation_adapt_{name}-O{opt}.wasm'
            text = run([validator, 'print', module]).stdout.decode()
            def emit(label, value):
                wat = out / f'negation-adapt-{name}-{label}-O{opt}.wat'; wasm = wat.with_suffix('.wasm')
                exports = ''.join(f'  (export "test_stack_top_{i}" (global {i}))\n' for i in range(2 if data else 1))
                wat.write_text(value[:value.rfind(')')] + exports + ')\n')
                run([validator, 'parse', wat, '-o', wasm]); run([validator, 'validate', wasm])
                return wasm
            args = [node, ROOT / 'test/wasm_negation_adaptation_owner.mjs']
            result = run(args + [emit('healthy', text), 'data' if data else 'frame'])
            assert result.stdout == b'before\nafter=2,false,false\n' and not result.stderr
            count += 1
            a, z = function_span(text, 'main'); body = text[a:z]
            missing, n = re.subn(r'(?m)^\s*f32\.neg\s*$', '', body); assert n == 1
            wrong_op, n = re.subn(r'\bf64\.neg\b', 'f64.abs', body); assert n == 1
            wrong_offset, n = re.subn(r'\bf64\.store( 1)? offset=6\b', r'f64.store\1 offset=7', body); assert n == 1
            wrong_count, n = re.subn(HEADER, lambda m: m['op'] + '3' + m['tail'], body); assert n == 1
            wrong_bound, n = re.subn(r'(i64\.const )2(\n\s*i64\.ge_u\b)', r'\g<1>3\2', body); assert n == 1
            cases = [('missing-negation', missing), ('wrong-op', wrong_op), ('wrong-offset', wrong_offset),
                     ('wrong-count', wrong_count), ('wrong-bound', wrong_bound)]
            if data:
                wrong_memory, n = re.subn(r'\bf32\.store 1\b', 'f32.store', body); assert n == 1
                cases.append(('wrong-memory', wrong_memory))
            for label, modified in cases:
                damaged = emit(label, text[:a] + modified + text[z:])
                result = run(args + [damaged, 'data' if data else 'frame'], ok=False)
                reason = (b'adapted negation data memory image differs' if data and label != 'wrong-memory' else
                          b'adapted negation memory 0 image differs')
                assert result.returncode == 1 and reason in result.stderr, (label, result.stderr)
                count += 1
    return count


def check_prefixes(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        for capacity in (255, 256, 65535, 65536):
            module = out / f'wasm_fixed_negation_adapt_prefix_{capacity}-O{opt}.wasm'
            text = run([validator, 'print', module]).stdout.decode()
            def emit(label, value):
                wat = out / f'negation-adapt-prefix-{capacity}-{label}-O{opt}.wat'; wasm = wat.with_suffix('.wasm')
                wat.write_text(value[:value.rfind(')')] + '  (export "test_stack_top_0" (global 0))\n)\n')
                run([validator, 'parse', wat, '-o', wasm]); run([validator, 'validate', wasm])
                return wasm
            args = [node, ROOT / 'test/wasm_negation_adaptation_prefix.mjs']
            result = run(args + [emit('healthy', text), str(capacity)])
            assert result.stdout == b'before\nafter=2,-19088743,19088743\n' and not result.stderr
            count += 1
            a, z = function_span(text, 'main'); body = text[a:z]
            modified, n = re.subn(HEADER, lambda m: m['op'] + '3' + m['tail'], body); assert n == 1
            result = run(args + [emit('wrong-count', text[:a] + modified + text[z:]), str(capacity)], ok=False)
            assert result.returncode == 1 and b'adapted negation prefix memory image differs' in result.stderr
            count += 1
    return count


def check_loop(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        module = out / f'wasm_fixed_negation_adapt_loop_exit-O{opt}.wasm'
        text = run([validator, 'print', module]).stdout.decode()
        def emit(label, value):
            wat = out / f'negation-adapt-loop-{label}-O{opt}.wat'; wasm = wat.with_suffix('.wasm')
            wat.write_text(value[:value.rfind(')')] + '  (export "test_stack_top_0" (global 0))\n)\n')
            run([validator, 'parse', wat, '-o', wasm]); run([validator, 'validate', wasm])
            return wasm
        args = [node, ROOT / 'test/wasm_negation_adaptation_loop.mjs']
        result = run(args + [emit('healthy', text)])
        assert result.stdout == b'head\nhead\nhead\nhead\nloop_exit\n' and not result.stderr
        count += 1
        a, z = function_span(text, 'main'); body = text[a:z]
        restores = list(re.finditer(r'(?m)^\s*global\.set 0\s*$', body)); assert len(restores) >= 2
        restore = restores[0]
        modified = body[:restore.start()] + '\n      drop\n' + body[restore.end():]
        result = run(args + [emit('missing-source-restore', text[:a] + modified + text[z:])], ok=False)
        assert result.returncode == 1 and b'adapted negation loop live frame top differs' in result.stderr
        count += 1
    return count
