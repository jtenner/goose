"""Specific packed-struct regression controls for validated test modules."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def check_modules(run, node, validator, wasmtime_python, out):
    count = 0
    source = ROOT / 'test/wasm/wasm_struct_values.goose'
    line = next(i for i, text in enumerate(source.read_text().splitlines(), 1)
                if 'assert(n.mixed.c == m.c)' in text)
    prefix = b''.join((ROOT / 'test/expected/wasm_struct_values.out').read_bytes()
                      .splitlines(keepends=True)[:2])
    for opt in (0, 2):
        module = out / f'wasm_struct_values-O{opt}.wasm'
        text = run([validator, 'print', module]).stdout.decode()
        pattern = r'i64\.store8 offset=8(?=\s|\))'
        assert len(re.findall(pattern, text)) == 1, 'missing unique nested byte-store control site'
        control = out / f'struct-wrong-width-O{opt}.wat'
        control.write_text(re.sub(pattern, 'i64.store offset=8', text))
        broken = control.with_suffix('.wasm')
        run([validator, 'parse', control, '-o', broken])
        run([validator, 'validate', broken])
        engines = [[node, ROOT / 'scripts/run_wasm.mjs', broken]]
        if wasmtime_python:
            engines.append([wasmtime_python, ROOT / 'test/wasmtime_host.py', broken])
        for command in engines:
            result = run(command, ok=False)
            assert result.returncode and b'assert failed' in result.stderr
            assert f'{source}:{line}'.encode() in result.stderr, 'control failed at another source location'
            assert result.stdout == prefix, 'control did not reach the neighboring-field assertion'
            count += 1
        module = out / f'wasm_struct_hidden-O{opt}.wasm'
        text = run([validator, 'print', module]).stdout.decode()
        functions = [text for text in text.splitlines() if re.search(r'\(func \$bounce\.', text)]
        assert len(functions) == 1 and '(param i64 i64) (result i64)' in functions[0], functions
        count += 1
    return count


def check_constructor_locals(run, exe, node, validator, wasmtime_python, out, local_counts):
    root = Path(__file__).resolve().parents[1]
    observed = []
    for length in (32, 256):
        values = ', '.join(str(i % 251) for i in range(length))
        source = out / f'struct-local-count-{length}.goose'
        source.write_text('struct S { items: i64[..1024], after: i64 }\n'
                          'fn main() { var s: S = S { items: [' + values + '], after: 99 }; '
                          f'print(s.items.len, ",", s.items[{length - 1}], ",", s.after); }}\n')
        expected = f'{length},{(length - 1) % 251},99\n'.encode()
        for opt in (0, 2):
            module = out / f'struct-local-count-{length}-O{opt}.wasm'
            run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, source])
            counts = local_counts(module.read_bytes())
            assert max(counts) <= 64, 'struct field constructor scratch grew with literal length'
            observed.append(counts)
            run([validator, 'validate', module])
            assert run([node, root / 'scripts/run_wasm.mjs', module]).stdout == expected
            if wasmtime_python:
                assert run([wasmtime_python, root / 'test/wasmtime_host.py', module]).stdout == expected
    assert all(counts == observed[0] for counts in observed), observed
    return len(observed)
