"""Check guards retained by copied data-aggregate iteration."""
import re


def check_admission(run, exe, out, node='node', validator='wasm-tools', wasmtime_python=None):
    cases = []
    for binder in ('s', '&s'):
        suffix = 'ref' if binder.startswith('&') else 'copy'
        cases.append(('owner-field-' + suffix,
                      'struct S { n: i64 }\nstruct Holder { rows: S[]& }\n'
                      'fn main() { var rows: S[] = [S { n: 7 }]; '
                      'var holder: Holder = Holder { rows: rows }; '
                      f'for {binder} in holder.rows {{ assert(s.n == 7); }} }}\n'))
        cases.append(('inline-field-' + suffix,
                      'struct S { n: i64 }\nstruct Row { cells: S[1] }\n'
                      'fn main() { var rows: Row[] = [Row { cells: [S { n: 7 }] }]; '
                      f'for {binder} in rows[0].cells {{ assert(s.n == 7); }} }}\n'))
    count = 0
    for name, text in cases:
        source = out / ('data-iteration-' + name + '.goose'); source.write_text(text)
        for opt in (0, 2):
            prefix = out / f'data-iteration-{name}-O{opt}'
            run([exe, f'-O{opt}', '--standalone', '-o', prefix.with_suffix('.c'), source])
            wasm = prefix.with_suffix('.wasm')
            run([exe, f'-O{opt}', '--target', 'wasm', '-o', wasm, source])
            run([validator, 'validate', wasm])
            from pathlib import Path
            root = Path(__file__).resolve().parents[1]
            engines = [[node, root / 'scripts/run_wasm.mjs', wasm]]
            if wasmtime_python:
                engines.append([wasmtime_python, root / 'test/wasmtime_host.py', wasm])
            for args in engines:
                result = run(args)
                assert not result.stdout and not result.stderr, (name, result.stdout, result.stderr)
                count += 1
    source = out / 'data-iteration-readonly.goose'
    source.write_text('struct S { n: i64 }\nfn main() { var rows: S[] = [S { n: 7 }]; '
                      'for s in rows { s.n += 1; } }\n')
    rejected = run([exe, '--check', source], ok=False)
    assert rejected.returncode == 1 and (
        b'cannot write s: a by-value binding is a copy of the element; '
        b'bind it by reference (&s) to write the element') in rejected.stderr, rejected.stderr
    count += 1
    source = out / 'data-iteration-frame-limit.goose'
    source.write_text('struct S { bytes: u8[2147483648] }\n'
                      'recursive fn probe(rows: S[]&) { '
                      'for a in rows { assert(a.bytes[0] == 0); } '
                      'for b in rows { assert(b.bytes[0] == 0); } }\n'
                      'fn main() { var rows: S[] = []; probe(rows); }\n')
    for opt in (0, 2):
        prefix = out / f'data-iteration-frame-limit-O{opt}'
        # Establish front-end admission only. Never compile or run this huge C image.
        run([exe, f'-O{opt}', '--standalone', '-o', prefix.with_suffix('.c'), source])
        wasm = prefix.with_suffix('.wasm')
        rejected = run([exe, f'-O{opt}', '--target', 'wasm', '-o', wasm, source], ok=False)
        assert rejected.returncode == 1 and re.findall(
            rb'wasm target: ([^\n]+)', rejected.stderr) == [b'frame exceeds memory32'], rejected.stderr
        assert not wasm.exists()
        count += 1
    return count
