"""Fixed to limited construction: payload boundaries, spare bytes and owner tops."""
from pathlib import Path
import re
from wasm_data_iteration_checks import function_span
from wasm_fixed_binary_checks import emit
ROOT = Path(__file__).resolve().parents[1]


def change_size(body, size):
    copies = list(re.finditer(r'local.get (\d+)\n\s*memory.copy\b', body))
    assert len(copies) == 1
    local = copies[0][1]
    result, n = re.subn(rf'i32.const 16(?=\n\s*local.set {local}\b)', f'i32.const {size}', body)
    assert n == 1
    return result


def check_owners(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        for mode in ('stored', 'call'):
            text = run([validator, 'print', out / f'wasm_fixed_array_layout_owner_{mode}-O{opt}.wasm']).stdout.decode()
            args = [node, ROOT / 'test/wasm_fixed_array_layout_owner.mjs']
            def observed(label, value, ok=True):
                module = emit(run, validator, out, f'fixed-layout-{mode}-{label}-O{opt}', value)
                return run(args + [module, mode], ok=ok)
            result = observed('healthy', text)
            assert result.stdout == b'before\nafter\n' and not result.stderr
            count += 1
            a, z = function_span(text, 'main'); body = text[a:z]
            prefix, n = re.subn(r'i64.const 2(?=\n\s*i64.store8\b)', 'i64.const 3', body); assert n == 1
            restore, n = re.subn(r'global.set 0\b', 'drop', body, count=1); assert n == 1
            for label, modified, reason in [
                ('short', change_size(body, 8), b'limited conversion memory 0 image differs'),
                ('long', change_size(body, 24), b'limited conversion memory 0 image differs'),
                ('prefix', prefix, b'limited conversion memory 0 image differs'),
                ('restore', restore, b'limited conversion live frame top differs' if mode == 'call'
                 else b'limited conversion completed frame top differs'),
            ]:
                result = observed(label, text[:a] + modified + text[z:], False)
                assert result.returncode == 1 and reason in result.stderr, (mode, label, result.stderr)
                count += 1
    return count


def check_data(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        text = run([validator, 'print', out / f'wasm_fixed_array_layout_wide_data_owner-O{opt}.wasm']).stdout.decode()
        args = [node, ROOT / 'test/wasm_fixed_array_layout_data.mjs']
        def observed(label, value, ok=True):
            module = emit(run, validator, out, f'fixed-layout-data-{label}-O{opt}', value, 2)
            return run(args + [module], ok=ok)
        result = observed('healthy', text)
        assert result.stdout == b'before\nafter\n' and not result.stderr
        count += 1
        a, z = function_span(text, 'main'); body = text[a:z]
        prefix, n = re.subn(r'i64.store16 1 offset=5\b', 'i64.store8 1 offset=5', body); assert n == 1
        release, n = re.subn(r'memory.copy 1 0\b', 'memory.copy 1 0\n      i32.const 1\n      global.set 1', body); assert n == 1
        memory, n = re.subn(r'memory.copy 1 0\b', 'memory.copy', body); assert n == 1
        for label, modified, reason in [
            ('short', change_size(body, 8), b'limited data conversion data image differs'),
            ('long', change_size(body, 24), b'limited data conversion data image differs'),
            ('prefix-width', prefix, b'limited data conversion data image differs'),
            ('release', release, b'limited data conversion live data top differs'),
            ('wrong-memory', memory, b'limited data conversion memory 0 image differs'),
        ]:
            result = observed(label, text[:a] + modified + text[z:], False)
            assert result.returncode == 1 and reason in result.stderr, (label, result.stderr)
            count += 1
    return count
