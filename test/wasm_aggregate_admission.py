"""Native-valid deferred operations for Memory 0 aggregate arrays."""
from pathlib import Path

CASES = {'default': ['struct S { x: i64 = 7 }\nfn main() { var a: S[2] = default<S[2]>(); print(a[0].x); }\n',
             ['aggregate array defaults']],
 'limited-default': ['struct S { x: i64 = 7 }\n'
                     'fn main() { var a: S[..3] = default<S[..3]>(); print(a.len); }\n',
                     ['aggregate array defaults']],
 'fill': ['struct S { x: i64 = 7 }\n'
          'fn main() { var s: S = S { x: 9 }; var a: S[2] = [s; 2]; print(a[1].x); }\n',
          ['aggregate array fills']],
 'zero-fill': ['var calls: i64 = 0; fn tick() -> i64 { calls++; return calls; }\n'
               'struct S { x: i64 = 7 }\n'
               'fn main() { var a: S[0] = [S { x: tick() }; 0]; assert(calls == 1); print(a.len); }\n',
               ['aggregate array fills']],
 'push': ['struct S { x: i64 = 7 }\n'
          'fn main() { var a: S[..3] = [S { x: 1 }]; var s: S = S { x: 2 }; a.push(s); print(a.len); '
          '}\n',
          ['aggregate push/pop', 'aggregate values need']],
 'pop': ['struct S { x: i64 = 7 }\n'
         'fn main() { var a: S[..3] = [S { x: 1 }]; var s: S = a.pop(); print(s.x); }\n',
         ['aggregate results need', 'aggregate push/pop', 'aggregate values need']],
 'discard-pop': ['struct S { x: i64 = 7 }\n'
                 'fn main() { var a: S[..3] = [S { x: 1 }]; a.pop(); print(a.len); }\n',
                 ['aggregate push/pop', 'aggregate values need']],
 'equality': ['struct S { x: i64 = 7 }\n'
              'fn main() { var a: S[1] = [S { x: 1 }]; var b: S[1] = [S { x: 1 }]; print(a == b); }\n',
              ['aggregate array equality']],
 'assign': ['struct S { x: i64 = 7 }\n'
            'fn main() { var a: S[1] = [S { x: 1 }]; var b: S = S { x: 2 }; a[0] = b; print(a[0].x); '
            '}\n',
            ['whole-aggregate assignment']],
 'adaptation': ['struct S { x: i64 = 7 }\n'
                'fn main() { var a: S[1] = [S { x: 1 }]; var b: S[..2] = a; print(b[0].x); }\n',
                ['array adaptation']],
 'data-varint': ['struct Row { cells: u16[2] }\n'
          'recursive fn read(a: u16[2]&) -> i64 { a[1] }\n'
          'fn main() { var rows: Row[varint] = [Row { cells: [11, 22] }]; print(read(rows[0].cells)); }\n',
          ['compound array elements']],
 'nested': ['struct S { x: i64 = 7 }\n'
            'fn main() { var a: S[1][1] = [[S { x: 1 }]]; print(a[0][0].x); }\n',
            ['compound array elements']],
 'field-iteration': ['struct S { x: i64 = 7 }\n'
                     'struct H { items: S[1] }\n'
                     'fn main() { var h: H = H { items: [S { x: 1 }] }; for &s in h.items { print(s.x); '
                     '} }\n',
                     ['field-path iteration']],
 'argument': ['struct S { x: i64 }\n'
              'recursive fn read(a: S[1]) -> i64 { a[0].x }\n'
              'fn main() { var a: S[1] = [S { x: 1 }]; print(read(a)); }\n',
              ['by-value arrays']],
 'inline-argument': ['struct S { x: i64 }\n'
                     'inline fn read(a: S[1]) -> i64 { a[0].x }\n'
                     'fn main() { var a: S[1] = [S { x: 1 }]; print(read(a)); }\n',
                     ['by-value arrays']],
 'result': ['struct S { x: i64 }\n'
            'recursive fn make(n: i64) -> S[1] { [S { x: n }] }\n'
            'fn main() { var a: S[1] = make(1); print(a[0].x); }\n',
            ['array results']],
 'callback-argument': ['struct S { x: i64 }\n'
                       'fn invoke<F>(a: S[1]&) { F(copy(a)); }\n'
                       'fn main() { var a: S[1] = [S { x: 1 }]; invoke(a) { p: S[1] => print(p[0].x); '
                       '}; }\n',
                       ['by-value arrays']],
 'array-assign': ['struct S { x: i64 }\n'
                  'fn main() { var a: S[1] = [S { x: 1 }]; var b: S[1] = [S { x: 2 }]; a = b; '
                  'print(a[0].x); }\n',
                  ['whole-array assignment']]}


def check_admission(run, exe, cc, out, node='node', validator='wasm-tools', wasmtime_python=None):
    root = Path(__file__).resolve().parents[1]
    count = 0
    for name, (source, reasons) in CASES.items():
        path = out / ('aggregate-admission-' + name + '.goose'); path.write_text(source)
        for opt in (0, 2):
            prefix = out / f'aggregate-admission-{name}-O{opt}'
            c, binary, module = (prefix.with_suffix(ext) for ext in ('.c', '.native', '.wasm'))
            run([exe, f'-O{opt}', '--standalone', '-o', c, path])
            run([cc, '-O0', c, '-pthread', '-lm', '-ldl', '-o', binary])
            reference = run([binary])
            module.unlink(missing_ok=True)
            result = run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, path], ok=False)
            if name in ('field-iteration', 'assign', 'default', 'limited-default', 'fill', 'zero-fill', 'array-assign', 'argument', 'inline-argument', 'callback-argument', 'result', 'adaptation'):
                assert not result.returncode and not result.stderr
                run([validator, 'validate', module])
                assert run([node, root / 'scripts/run_wasm.mjs', module]).stdout == reference.stdout
                assert reference.stdout == {'field-iteration': b'1\n', 'assign': b'2\n',
                                            'default': b'7\n', 'limited-default': b'0\n',
                                            'fill': b'9\n', 'zero-fill': b'0\n',
                                            'array-assign': b'2\n', 'argument': b'1\n',
                                            'inline-argument': b'1\n', 'callback-argument': b'1\n',
                                            'result': b'1\n', 'adaptation': b'1\n'}[name]
                if wasmtime_python:
                    assert run([wasmtime_python, root / 'test/wasmtime_host.py', module]).stdout == reference.stdout
                count += 1
                continue
            assert result.returncode and b'wasm target: ' in result.stderr, (name, opt, result.stderr)
            assert any(reason.encode() in result.stderr for reason in reasons), (name, opt, result.stderr)
            assert not module.exists(), (name, opt, 'partial unsupported module')
            count += 1
    return count


def check_limits(run, exe, out):
    # Native emission establishes frontend validity. These cases never compile
    # or execute the generated C and never allocate the declared large images.
    cases = {
        'product': ('struct S { x: u64 }\n'
                    'recursive fn present(a: S[536870912]?) -> bool { a != null }\n'
                    'fn main() { print(present(null)); }\n',
                    b'fixed aggregate layout exceeds memory32'),
        'prefix': ('struct S { x: u8 }\n'
                   'recursive fn present(a: S[..4294967292]?) -> bool { a != null }\n'
                   'fn main() { print(present(null)); }\n',
                   b'fixed aggregate layout exceeds memory32'),
        'frame': ('struct S { x: i64 }\n'
                  'fn main() { var a: S[..268435456] = [S { x: 1 }]; '
                  'var b: S[..268435456] = [S { x: 2 }]; '
                  'assert(&a .!= &b); print(a[0].x, b[0].x); }\n',
                  b'frame exceeds memory32'),
    }
    count = 0
    for name, (source, reason) in cases.items():
        path = out / f'aggregate-limit-{name}.goose'; path.write_text(source)
        for opt in (0, 2):
            c = out / f'aggregate-limit-{name}-O{opt}.c'
            run([exe, f'-O{opt}', '--standalone', '-o', c, path])
            module = c.with_suffix('.wasm'); module.unlink(missing_ok=True)
            result = run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, path], ok=False)
            assert result.returncode and reason in result.stderr and not module.exists(), (name, opt, result.stderr)
            count += 1
    return count
