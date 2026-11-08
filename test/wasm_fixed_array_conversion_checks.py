"""Fixed-value array receivers: images, prefix bounds and live owner scopes."""
from pathlib import Path
import re
from wasm_data_iteration_checks import function_span
from wasm_fixed_binary_checks import emit
ROOT = Path(__file__).resolve().parents[1]
COPY = r'memory.copy 1(?: 0)?\b'


def change_copy(body, size, replacement):
    modified, n = re.subn(rf'i32.const {size}(?=\n\s*{COPY})', f'i32.const {replacement}', body)
    assert n == 1
    return modified


def premature(body):
    modified, n = re.subn(COPY, lambda m: m[0] + '\n      i32.const 1\n      global.set 1', body)
    assert n == 1
    return modified


def check_owners(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        for mode in ('variable', 'varint', 'limited', 'grow', 'stored'):
            text = run([validator, 'print', out / f'wasm_fixed_array_conversion_owner_{mode}-O{opt}.wasm']).stdout.decode()
            args = [node, ROOT / 'test/wasm_fixed_array_conversion_owner.mjs']
            def observed(label, value, ok=True):
                module = emit(run, validator, out, f'fixed-array-owner-{mode}-{label}-O{opt}', value, 2)
                return run(args + [module, mode], ok=ok)
            result = observed('healthy', text)
            assert result.stdout == b'before\nafter\n' and not result.stderr
            count += 1
            a, z = function_span(text, 'main'); body = text[a:z]
            wrong_memory, n = re.subn(COPY, 'memory.copy', body); assert n == 1
            for label, modified, reason in [
                ('short-copy', change_copy(body, 16, 8), b'fixed array conversion data image differs'),
                ('long-copy', change_copy(body, 16, 24), b'fixed array conversion data image differs'),
                ('early-release', premature(body), b'fixed array conversion live data top differs'),
                ('wrong-memory', wrong_memory, b'fixed array conversion memory 0 image differs'),
            ]:
                result = observed(label, text[:a] + modified + text[z:], ok=False)
                assert result.returncode == 1 and reason in result.stderr, (mode, label, result.stderr)
                count += 1
    return count


def check_prefixes(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        for size in (0, 127, 128, 16383, 16384):
            text = run([validator, 'print', out / f'wasm_fixed_array_conversion_prefix_{size}-O{opt}.wasm']).stdout.decode()
            args = [node, ROOT / 'test/wasm_fixed_array_conversion_prefix.mjs']
            def observed(label, value, ok=True):
                module = emit(run, validator, out, f'fixed-array-prefix-{size}-{label}-O{opt}', value, 2)
                return run(args + [module, str(size)], ok=ok)
            result = observed('healthy', text)
            assert result.stdout == b'before\nafter\n' and not result.stderr
            count += 1
            a, z = function_span(text, 'main'); body = text[a:z]
            prefix, n = re.subn(r'(?m)^(\s*)i64.store8 1\b',
                                r'\1i64.const 1\n\1i64.xor\n\1i64.store8 1', body, count=1)
            assert n == 1
            for label, modified, reason in [
                ('wrong-prefix', prefix, b'fixed array prefix data image differs'),
                ('wrong-bound', change_copy(body, size, size - 1 if size else 1), b'fixed array prefix data image differs'),
                ('early-release', premature(body), b'fixed array prefix live data top differs'),
            ]:
                result = observed(label, text[:a] + modified + text[z:], ok=False)
                assert result.returncode == 1 and reason in result.stderr, (size, label, result.stderr)
                count += 1
    return count


def check_padded(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        text = run([validator, 'print', out / f'wasm_fixed_array_conversion_padded_data-O{opt}.wasm']).stdout.decode()
        args = [node, ROOT / 'test/wasm_fixed_array_conversion_padded.mjs']
        def observed(label, value, ok=True):
            return run(args + [emit(run, validator, out, f'fixed-array-padded-{label}-O{opt}', value, 2)], ok=ok)
        result = observed('healthy', text)
        assert result.stdout == b'before\nafter\n' and not result.stderr
        count += 1
        a, z = function_span(text, 'main'); body = text[a:z]
        wrong, n = re.subn(r'\bf32.add\b', 'f32.sub', body); assert n == 1
        pad, n = re.subn(COPY, lambda m: m[0] + '\n      i32.const 9\n      i32.const 0\n      i32.store8 1', body)
        assert n == 1
        for label, modified, reason in [
            ('wrong-op', wrong, b'fixed array padded memory 0 image differs'),
            ('padding', pad, b'fixed array padded data image differs'),
            ('short-copy', change_copy(body, 28, 24), b'fixed array padded data image differs'),
            ('early-release', premature(body), b'fixed array padded live data top differs'),
        ]:
            result = observed(label, text[:a] + modified + text[z:], ok=False)
            assert result.returncode == 1 and reason in result.stderr, (label, result.stderr)
            count += 1
    return count


def check_loop(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        text = run([validator, 'print', out / f'wasm_fixed_array_conversion_early_continue-O{opt}.wasm']).stdout.decode()
        args = [node, ROOT / 'test/wasm_fixed_array_conversion_loop.mjs']
        result = run(args + [emit(run, validator, out, f'fixed-array-loop-healthy-O{opt}', text, 2)])
        assert result.stdout == b'head\n'*4 + b'after\nearly_continue\n' and not result.stderr
        count += 1
        a, z = function_span(text, 'main'); body = text[a:z]
        modified, n = re.subn(r'(?m)^\s*global.set 1\s*$', '\n      drop\n', body); assert n == 1
        result = run(args + [emit(run, validator, out, f'fixed-array-loop-missing-restore-O{opt}',
                                 text[:a] + modified + text[z:], 2)], ok=False)
        assert result.returncode == 1 and b'fixed array conversion loop live data top differs' in result.stderr
        count += 1
    return count


def check_namespaces(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        text = run([validator, 'print', out / f'wasm_fixed_array_conversion_namespaces-O{opt}.wasm']).stdout.decode()
        args = [node, ROOT / 'test/wasm_fixed_array_conversion_namespaces.mjs']
        result = run(args + [emit(run, validator, out, f'fixed-array-namespaces-healthy-O{opt}', text, 3)])
        assert result.stdout == b'inside\ninside\nnamespaces\n' and not result.stderr
        count += 1
        builds = list(re.finditer(r'(?m)^  \(func \$build\.\d+(?=\s|\()', text))
        assert len(builds) == 2
        a = builds[1].start(); z = text.index('\n  (func ', a + 1); body = text[a:z]
        assert re.search(r'\(param i64 i64\)', body) and 'memory.copy 2 0' in body
        modified, n = re.subn(r'call \$goose.reserve_memory\.2\b', 'call $goose.reserve_memory.1', body)
        assert n == 1
        result = run(args + [emit(run, validator, out, f'fixed-array-namespaces-wrong-base-O{opt}',
                                 text[:a] + modified + text[z:], 3)], ok=False)
        assert result.returncode == 1 and b'fixed array conversion namespace tops differ' in result.stderr
        count += 1
    return count


def check_global(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        text = run([validator, 'print', out / f'wasm_fixed_array_conversion_global-O{opt}.wasm']).stdout.decode()
        args = [node, ROOT / 'test/wasm_fixed_array_conversion_global.mjs']
        result = run(args + [emit(run, validator, out, f'fixed-array-global-healthy-O{opt}', text, 2)])
        assert result.stdout == b'global\n' and not result.stderr
        count += 1
        a, z = function_span(text, 'main'); body = text[a:z]; end = body.rfind(')'); assert end >= 0
        modified = body[:end] + '    global.get 1\n    i32.const 1\n    i32.add\n    global.set 1\n  ' + body[end:]
        result = run(args + [emit(run, validator, out, f'fixed-array-global-wrong-top-O{opt}',
                                 text[:a] + modified + text[z:], 2)], ok=False)
        assert result.returncode == 1 and b'fixed array global data top differs' in result.stderr
        count += 1
    return count
