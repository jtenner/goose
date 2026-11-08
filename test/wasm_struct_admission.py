"""Native-valid aggregate admission checks; no aggregate ABI is inferred from scalar handles."""
from pathlib import Path

CASES = {'argument': ('struct S { x: i64 }\n'
              'recursive fn read(s: S) -> i64 { s.x }\n'
              'fn main() { var s: S = S { x: 1 }; print(read(s)); }\n',
              'by-value aggregates'),
 'inline-argument': ('struct S { x: i64 }\n'
                     'inline fn read(s: S) -> i64 { s.x }\n'
                     'fn main() { var s: S = S { x: 1 }; print(read(s)); }\n',
                     'by-value aggregates'),
 'result': ('struct S { x: i64 }\n'
            'recursive fn make(n: i64) -> S { S { x: n } }\n'
            'fn main() { var s: S = make(1); print(s.x); }\n',
            'by-value aggregates'),
 'inline-result': ('struct S { x: i64 }\n'
                   'inline fn make(n: i64) -> S { S { x: n } }\n'
                   'fn main() { var s: S = make(1); print(s.x); }\n',
                   'by-value aggregates'),
 'assign': ('struct S { x: i64 }\n'
            'fn main() { var a: S = S { x: 1 }; var b: S = S { x: 2 }; a = b; print(a.x); }\n',
            'whole-aggregate assignment'),
 'field-assign': ('struct S { x: i64 }\n'
                  'struct Outer { s: S }\n'
                  'fn main() { var a: Outer = Outer { s: S { x: 1 } }; var b: S = S { x: 2 }; a.s '
                  '= b; print(a.s.x); }\n',
                  'whole-aggregate assignment'),
 'element-assign': ('struct S { x: i64 }\n'
                    'fn main() { var a: S = S { x: 1 }; var b: S = S { x: 2 }; var refs: S&[1] = '
                    '[a]; refs[0] = b; print(a.x); }\n',
                    'whole-aggregate assignment'),
 'value-equality': ('struct S { x: i64 }\n'
                    'fn main() { var a: S = S { x: 1 }; var b: S = S { x: 2 }; print(a == b); }\n',
                    'aggregate value operators'),
 'print': ('struct S { x: i64 }\nfn main() { var a: S = S { x: 1 }; print(a); }\n',
           'aggregate printing'),
 'field-for': ('struct S { x: i64 }\n'
               'struct Outer { items: i64[2] }\n'
               'fn main() { var a: Outer = Outer { items: [1, 2] }; for v in a.items { print(v); } '
               '}\n',
               'field-path iteration'),
 'wide-count-elements': ('struct S { x: i64 }\nfn main() { var a: S[u64] = [S { x: 1 }]; print(a[0].x); }\n',
              'compound array elements'),
 'variable-field': ('struct S { x: i64 }\n'
                    'struct V { data: i64[] }\n'
                    'fn main() { var a: V = V { data: [1] }; print(a.data[0]); }\n',
                    'nonfixed'),
 'uninitialized': ('struct S { x: i64 }\nfn main() { var a: S; a = S { x: 1 }; print(a.x); }\n',
                   'uninitialized aggregate'),
 'temporary': ('struct S { x: i64 }\nfn main() { print((S { x: 1 }).x); }\n',
               'aggregate temporaries'),
 'function-value-argument': ('struct S { x: i64 }\n'
                             'fn apply<F>(x: S&) -> i64 { F(copy(x)) }\n'
                             'fn main() { var s: S = S { x: 1 }; print(apply(s) { y => y.x }); }\n',
                             'by-value aggregates'),
 'function-value-result': ('struct S { x: i64 }\n'
                           'fn apply<F>(n: i64) -> i64 { var s: S = F(n); s.x }\n'
                           'fn main() { print(apply(1) { y => S { x: y } }); }\n',
                           'aggregate results'),
 'field-adaptation': ('struct S { x: i64 }\n'
                      'struct A { xs: u8[3] }\n'
                      'struct B { xs: u8[..4] }\n'
                      'fn main() { var a: A = A { xs: [1, 2, 3] }; var b: B = B { xs: a.xs }; '
                      'print(b.xs[0]); }\n',
                      'aggregate adaptation')}

def check_admission(run, exe, node, validator, wasmtime_python, out):
    root = Path(__file__).resolve().parents[1]
    count = 0
    for name, (source, reason) in CASES.items():
        path = out / ('struct-admission-' + name + '.goose')
        path.write_text(source)
        for opt in (0, 2):
            prefix = out / f'struct-admission-{name}-O{opt}'
            c, module = prefix.with_suffix('.c'), prefix.with_suffix('.wasm')
            run([exe, f'-O{opt}', '--standalone', '-o', c, path])
            module.unlink(missing_ok=True)
            result = run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, path], ok=False)
            if name == 'inline-result' and opt == 2:
                # No call/result boundary remains: the optimizer left a fresh literal.
                assert not result.returncode and not result.stderr
                run([validator, 'validate', module])
                assert run([node, root / 'scripts/run_wasm.mjs', module]).stdout == b'1\n'
                if wasmtime_python:
                    assert run([wasmtime_python, root / 'test/wasmtime_host.py', module]).stdout == b'1\n'
            elif name in ('argument', 'inline-argument', 'function-value-argument',
                           'result', 'inline-result', 'function-value-result', 'temporary', 'field-adaptation'):
                assert not result.returncode and not result.stderr
                run([validator, 'validate', module])
                assert run([node, root / 'scripts/run_wasm.mjs', module]).stdout == b'1\n'
                if wasmtime_python:
                    assert run([wasmtime_python, root / 'test/wasmtime_host.py', module]).stdout == b'1\n'
            elif name == 'field-for':
                assert not result.returncode and not result.stderr
                run([validator, 'validate', module])
                assert run([node, root / 'scripts/run_wasm.mjs', module]).stdout == b'1\n2\n'
                if wasmtime_python:
                    assert run([wasmtime_python, root / 'test/wasmtime_host.py', module]).stdout == b'1\n2\n'
            elif name in ('assign', 'field-assign', 'element-assign'):
                assert not result.returncode and not result.stderr
                run([validator, 'validate', module])
                assert run([node, root / 'scripts/run_wasm.mjs', module]).stdout == b'2\n'
                if wasmtime_python:
                    assert run([wasmtime_python, root / 'test/wasmtime_host.py', module]).stdout == b'2\n'
            else:
                assert result.returncode and reason.encode() in result.stderr, (name, opt, result.stderr)
                assert not module.exists(), (name, opt, 'partial aggregate module')
            count += 1
    # These programs are compile-only. Never instantiate their declared huge images.
    limits = {
        'product': ('struct Huge { bytes: u64[576460752303423488] }\n'
                    'fn main() { var h: Huge = default<Huge>(); print(h.bytes[0]); }\n',
                    b'fixed aggregate layout exceeds memory32'),
        'layout-sum': ('struct Huge { a: u8[2147483648], b: u8[2147483648] }\n'
                       'fn main() { var h: Huge = default<Huge>(); print(h.a[0], h.b[0]); }\n',
                       b'fixed aggregate layout exceeds memory32'),
        'frame-sum': ('struct Huge { a: u8[2147483648] }\n'
                      'fn main() { var x: Huge = default<Huge>(); var y: Huge = default<Huge>(); print(x.a[0], y.a[0]); }\n',
                      b'frame exceeds memory32'),
    }
    for name, (source, reason) in limits.items():
        path = out / ('struct-limit-' + name + '.goose'); path.write_text(source)
        for opt in (0, 2):
            module = out / f'struct-limit-{name}-O{opt}.wasm'
            module.unlink(missing_ok=True)
            result = run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, path], ok=False)
            assert result.returncode and reason in result.stderr and not module.exists(), (name, opt, result.stderr)
            count += 1
    return count
