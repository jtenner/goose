"""Check current outer bounds and retain the nullable-field language guard."""


def check_paths(run, exe, cc, node, validator, wasmtime_python, out):
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    source = out / 'field-walk-bounds.goose'
    source.write_text('struct Row { values: i64[2] }\nstruct Holder { rows: Row[]& }\n'
                      'fn main() { var rows: Row[] = [Row { values: [1, 2] }]; '
                      'var empty: Row[] = []; var holder: Holder = Holder { rows: rows }; '
                      'for n, i in holder.rows[0].values { print("visit"); '
                      'if i == 0 { holder.rows .= empty; } } }\n')
    count = 0
    for opt in (0, 2):
        prefix = out / f'field-walk-bounds-O{opt}'
        c, native, wasm = (prefix.with_suffix(ext) for ext in ('.c', '.native', '.wasm'))
        run([exe, f'-O{opt}', '--standalone', '-o', c, source])
        run([cc, '-O0', c, '-pthread', '-lm', '-ldl', '-o', native])
        reference = run([native], ok=False)
        assert reference.returncode and b'index 0 out of bounds (length 0)' in reference.stderr
        assert reference.stdout == b'visit\n'
        run([exe, f'-O{opt}', '--target', 'wasm', '-o', wasm, source])
        run([validator, 'validate', wasm])
        engines = [[node, root / 'scripts/run_wasm.mjs', wasm]]
        if wasmtime_python:
            engines.append([wasmtime_python, root / 'test/wasmtime_host.py', wasm])
        for args in engines:
            result = run(args, ok=False)
            assert result.returncode and b'array index out of bounds' in result.stderr, result.stderr
            assert f'{source}:3'.encode() in result.stderr, result.stderr
            assert result.stdout == reference.stdout
            count += 1
    source = out / 'field-walk-null-policy.goose'
    source.write_text('struct S { n: i64 }\nstruct Holder { rows: S[]? }\n'
                      'fn main() { var holder: Holder = Holder {}; for s in holder.rows { print(s.n); } }\n')
    result = run([exe, '--check', source], ok=False)
    assert result.returncode == 1 and b'cannot iterate a value of type S[]?' in result.stderr, result.stderr
    return count + 1
