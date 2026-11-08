"""Native-valid fixed-enum admission limits, separate from frontend rejection."""
from pathlib import Path

CASES = {'argument': ('enum E { A { x: i64 }, B }\n'
              'recursive fn read(e: E) -> i64 { match e { A p => p.x, B => 0 } }\n'
              'fn main() { var e: E = E.A { x: 1 }; print(read(e)); }\n',
              'value-producing matches'),
 'inline-argument': ('enum E { A { x: i64 }, B }\n'
                     'inline fn read(e: E) -> i64 { match e { A p => p.x, B => 0 } }\n'
                     'fn main() { var e: E = E.A { x: 1 }; print(read(e)); }\n',
                     'value-producing matches'),
 'result': ('enum E { A { x: i64 }, B }\n'
            'recursive fn make(n: i64) -> E { E.A { x: n } }\n'
            'fn main() { var e: E = make(1); match e { A p => print(p.x), B => print(0) } }\n',
            'by-value aggregates'),
 'assign': ('enum E { A { x: i64 }, B }\n'
            'fn main() { var a: E = E.A { x: 1 }; var b: E = E.B; a = b; match a { A p => print(p.x), B => '
            'print(0) } }\n',
            'whole-aggregate assignment'),
 'print': ('enum E { A { x: i64 }, B }\nfn main() { var a: E = E.A { x: 1 }; print(a); }\n',
           'aggregate printing'),
 'value-equality': ('enum E { A { x: i64 }, B }\n'
                    'fn main() { var a: E = E.A { x: 1 }; var b: E = E.B; print(a == b); }\n',
                    'aggregate value operators'),
 'wide-count-elements': ('enum E { A { x: i64 }, B }\n'
              'fn main() { var a: E[u64] = [E.A { x: 1 }]; match a[0] { A p => print(p.x), B => print(0) } '
              '}\n',
              'compound array elements'),
 'adaptation': ('enum E { A { x: i64 }, B }\n'
                'fn main() { var a: E.A = E.A { x: 1 }; var b: E = a; match b { A p => print(p.x), B => '
                'print(0) } }\n',
                'aggregate adaptation'),
 'match-value': ('enum E { A { x: i64 }, B }\n'
                 'fn main() { var a: E = E.A { x: 1 }; var n: i64 = match a { A p => p.x, B => 0 }; '
                 'print(n); }\n',
                 'value-producing matches'),
 'variable': ('enum V { A { bytes: u8[] }, B }\n'
              'fn main() { var a: V.. = V.A { bytes: [1] }; match a { A p => print(p.bytes[0]), B => '
              'print(0) } }\n',
              'nonfixed'),
 'element-assign': ('enum E { A { x: i64 }, B }\n'
                    'fn main() { var a: E = E.A { x: 1 }; var b: E = E.B; var refs: E&[1] = [a]; refs[0] = '
                    'b; match a { A p => print(p.x), B => print(0) } }\n',
                    'whole-aggregate assignment'),
 'uninitialized': ('enum E { A { x: i64 }, B }\n'
                   'fn main() { var a: E; a = E.B; match a { A p => print(p.x), B => print(0) } }\n',
                   'uninitialized aggregate')}

def check_admission(run, exe, cc, out, node='node', validator='wasm-tools', wasmtime_python=None):
    root = Path(__file__).resolve().parents[1]
    count = 0
    for name, (source, reason) in CASES.items():
        path = out / ('enum-admission-' + name + '.goose')
        path.write_text(source)
        for opt in (0, 2):
            prefix = out / f'enum-admission-{name}-O{opt}'
            c, binary, module = (prefix.with_suffix(ext) for ext in ('.c', '.native', '.wasm'))
            run([exe, f'-O{opt}', '--standalone', '-o', c, path])
            run([cc, '-O0', c, '-pthread', '-lm', '-ldl', '-o', binary])
            reference = run([binary])
            module.unlink(missing_ok=True)
            result = run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, path], ok=False)
            if name in ('assign', 'element-assign', 'result'):
                assert not result.returncode and not result.stderr
                run([validator, 'validate', module])
                expected = b'1\n' if name == 'result' else b'0\n'
                assert run([node, root / 'scripts/run_wasm.mjs', module]).stdout == reference.stdout == expected
                if wasmtime_python:
                    assert run([wasmtime_python, root / 'test/wasmtime_host.py', module]).stdout == reference.stdout
                count += 1
                continue
            assert result.returncode and b'wasm target: ' in result.stderr and reason.encode() in result.stderr, (name, opt, result.stderr)
            assert not module.exists(), (name, opt, 'partial enum module')
            count += 1
    limits = {
        'tag-sum': ('enum Huge { A { bytes: u8[4294967295] }, B }\n'
                    'fn main() { var a: Huge = default<Huge>(); match a { A p => print(p.bytes[0]), B => print(0) } }\n', b'fixed aggregate layout exceeds memory32'),
        'frame-sum': ('enum Huge { A { bytes: u8[2147483648] }, B }\n'
                      'fn main() { var a: Huge = default<Huge>(); var b: Huge = default<Huge>(); match a { A p => print(p.bytes[0]), B => print(0) }; match b { A p => print(p.bytes[0]), B => print(0) } }\n', b'frame exceeds memory32'),
    }
    for name, (source, reason) in limits.items():
        path = out / ('enum-limit-' + name + '.goose'); path.write_text(source)
        for opt in (0, 2):
            module = out / f'enum-limit-{name}-O{opt}.wasm'; module.unlink(missing_ok=True)
            result = run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, path], ok=False)
            assert result.returncode and reason in result.stderr and not module.exists(), (name, opt, result.stderr)
            count += 1
    return count
