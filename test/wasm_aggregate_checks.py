"""Controls for Memory 0 aggregate-array places and constructor bounds."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def check_controls(run, node, validator, wasmtime_python, out, *, source=None,
                   stem='wasm_aggregate_array_control'):
    source = source or ROOT / 'test/wasm/wasm_aggregate_array_control.goose'
    lines = source.read_text().splitlines()
    count = 0
    for opt in (0, 2):
        text = run([validator, 'print', out / f'{stem}-O{opt}.wasm']).stdout.decode()
        assert len(re.findall(r'i32\.const 7(?=\s+memory\.copy(?:\s|$))', text)) == 2
        patterns = [
            ('short-copy', r'i32\.const 7(?=\s+memory\.copy(?:\s|$))', 'i32.const 6',
             'assert(a[0].tail'),
            ('wrong-stride', r'i64\.const 7(?=\s+i64\.mul)', 'i64.const 8',
             'assert(a[1].mark'),
        ]
        for name, pattern, replacement, assertion in patterns:
            assert re.search(pattern, text), (name, 'missing control site')
            wat = out / f'aggregate-{name}-O{opt}.wat'
            wat.write_text(re.sub(pattern, replacement, text))
            module = wat.with_suffix('.wasm')
            run([validator, 'parse', wat, '-o', module]); run([validator, 'validate', module])
            engines = [[node, ROOT / 'scripts/run_wasm.mjs', module]]
            if wasmtime_python:
                engines.append([wasmtime_python, ROOT / 'test/wasmtime_host.py', module])
            line = next(i for i, value in enumerate(lines, 1) if assertion in value)
            for command in engines:
                result = run(command, ok=False)
                assert result.returncode and b'assert failed' in result.stderr, (name, result.stderr)
                assert f'{source}:{line}'.encode() in result.stderr, (name, 'wrong failure site', result.stderr)
                assert result.stdout == b'', (name, 'control passed its designated assertion')
                count += 1
        # The callback observes the guard while the owner's activation is live.
        # It does not inspect released object bytes to infer completion.
        assert 'test_frame_top' not in text
        export = '  (export "test_frame_top" (global 0))\n)\n'
        instrumented = text[:text.rfind(')')] + export
        wat = out / f'aggregate-owner-guard-O{opt}.wat'; wat.write_text(instrumented)
        module = wat.with_suffix('.wasm')
        run([validator, 'parse', wat, '-o', module]); run([validator, 'validate', module])
        good = run([node, ROOT / 'test/wasm_aggregate_guard.mjs', module, '14'])
        assert good.stdout == b'control\n' and not good.stderr
        broken = out / f'aggregate-long-copy-O{opt}.wat'
        broken.write_text(re.sub(r'i32\.const 7(?=\s+memory\.copy(?:\s|$))',
                                 'i32.const 8', instrumented))
        badmodule = broken.with_suffix('.wasm')
        run([validator, 'parse', broken, '-o', badmodule]); run([validator, 'validate', badmodule])
        result = run([node, ROOT / 'test/wasm_aggregate_guard.mjs', badmodule, '14'], ok=False)
        assert result.returncode and b'aggregate constructor crossed its planned owner image' in result.stderr
        assert result.stdout == b''
        count += 2
    return count


def check_reference_abi(run, validator, out):
    count = 0
    for mode, result in (('thin', 'i32'), ('packed', 'i64')):
        for opt in (0, 2):
            module = out / f'wasm_aggregate_array_walk_{mode}-O{opt}.wasm'
            text = run([validator, 'print', module]).stdout.decode()
            for name, signature in (('arrayref', f'(param {result}) (result {result})'),
                                    ('elementref', f'(param {result}) (result {result})')):
                found = [line for line in text.splitlines() if re.search(r'\(func \$' + name + r'\.', line)]
                assert len(found) == 1 and signature in found[0], (mode, opt, name, found)
                count += 1
            module = out / f'wasm_inline_ref_abi_{mode}-O{opt}.wasm'
            text = run([validator, 'print', module]).stdout.decode()
            signatures = [
                ('fixedref', f'(param {result}) (result {result})'),
                ('limitedref', f'(param {result}) (result {result})'),
                ('optionalref', f'(param {result} i32) (result {result})'),
                ('choose', f'(param {result} {result} i32) (result {result})'),
            ]
            if mode == 'packed':
                signatures.append(('headerref', '(param i32) (result i32)'))
            for name, signature in signatures:
                found = [line for line in text.splitlines() if re.search(r'\(func \$' + name + r'\.', line)]
                assert len(found) == 1 and signature in found[0], (mode, opt, name, found)
                count += 1
    return count


def check_footprint(run, exe, node, validator, wasmtime_python, out, local_counts):
    count = 0

    def check(module, source, opt, expected):
        run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, source])
        run([validator, 'validate', module])
        engines = [[node, ROOT / 'scripts/run_wasm.mjs', module]]
        if wasmtime_python:
            engines.append([wasmtime_python, ROOT / 'test/wasmtime_host.py', module])
        for command in engines:
            result = run(command)
            assert result.stdout == expected and not result.stderr

    for kind in ('named', 'literal'):
        observed = []
        for length in (32, 256):
            source = out / f'aggregate-local-{kind}-{length}.goose'
            values = ', '.join(['s'] * length if kind == 'named' else
                               [f'S {{ x: {i % 251} }}' for i in range(length)])
            source.write_text('struct S { x: i64 }\nfn main() { ' +
                              ('var s: S = S { x: 7 }; ' if kind == 'named' else '') +
                              f'var a: S[{length}] = [' + values + ']; ' +
                              f'print(a.len, ",", a[{length - 1}].x); }}\n')
            expected = f'{length},{7 if kind == "named" else (length - 1) % 251}\n'.encode()
            for opt in (0, 2):
                module = out / f'aggregate-local-{kind}-{length}-O{opt}.wasm'
                check(module, source, opt, expected)
                counts = local_counts(module.read_bytes())
                assert max(counts) <= 64, 'aggregate literal constructor added per-element scratch'
                observed.append(counts); count += 1
        assert all(value == observed[0] for value in observed), (kind, observed)
    sizes, locals_ = [], []
    for capacity in (32, 65536):
        source = out / f'aggregate-sparse-{capacity}.goose'
        source.write_text('struct S { x: i64 }\n' +
                          f'var a: S[..{capacity}] = [S {{ x: 7 }}];\n' +
                          f'fn main() {{ assert(a.len == 1); assert(a.cap == {capacity}); ' +
                          'assert(a[0].x == 7); print("sparse"); }\n')
        for opt in (0, 2):
            module = out / f'aggregate-sparse-{capacity}-O{opt}.wasm'
            check(module, source, opt, b'sparse\n')
            sizes.append(module.stat().st_size)
            locals_.append(local_counts(module.read_bytes())); count += 1
    assert max(sizes) < 16384 and max(sizes) - min(sizes) < 128, sizes
    assert all(value == locals_[0] for value in locals_), locals_
    return count
