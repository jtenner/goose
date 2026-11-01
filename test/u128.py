#!/usr/bin/env python3
"""Native u128 acceptance, independent of packed-word layouts; cleans all output."""
import os
import pathlib
import random
import shutil
import subprocess
import tempfile

MASK = (1 << 128) - 1

def main():
    goose = shutil.which('goose++')
    assert goose, 'goose++ required on PATH'
    checks = 0
    with tempfile.TemporaryDirectory(prefix='goose-u128-native-') as td:
        root = pathlib.Path(td)
        env = dict(os.environ, GOOSE_HOME=str(root/'home'))
        def run(args, expected=0):
            p = subprocess.run(list(map(str, args)), capture_output=True, text=True, env=env)
            assert (p.returncode == 0) == (expected == 0), (args, p.returncode, p.stdout[:2000], p.stderr[:4000])
            return p.stdout + p.stderr
        rng = random.Random(128)
        pairs = [(0, 1), (MASK, MASK), (1 << 64, 1 << 63), (1 << 127, 3)]
        pairs += [(rng.getrandbits(128), rng.getrandbits(128) or 1) for _ in range(20)]
        declarations = []
        calls = []
        expected = []
        for i, op in enumerate(['+', '-', '*', '/', '%', '&', '|', '^']):
            declarations.append(f'fn op{i}(a: u128, b: u128) -> u128 {{ a {op} b }}')
            for a, b in pairs:
                calls.append(f'print(op{i}({a}, {b}));')
                result = {'+': a+b, '-': a-b, '*': a*b, '/': a//b, '%': a%b,
                          '&': a&b, '|': a|b, '^': a^b}[op] & MASK
                expected.append(str(result))
        declarations += ['fn shift(a: u128, n: i64) -> u128 { a << n }',
                         'fn high(a: u128) -> u128 { a >> 64 }',
                         'fn classify(a: u128) -> i64 { match a { 18446744073709551616 => 1, 18446744073709551617..18446744073709551620 => 2, _ => 3 } }']
        calls += ['print(shift(1, 127));', 'print(high(340282366920938463463374607431768211455));',
                  'print(classify(18446744073709551618));',
                  'var values: u128[2] = [18446744073709551616, 340282366920938463463374607431768211455];',
                  'print(values[0]);', 'print(values[1]);',
                  'print(340282366920938463463374607431768211455 as! u64);',
                  'print(18446744073709551616 == 18446744073709551617);',
                  'const if 18446744073709551616 < 18446744073709551617 { print(7); } else { print(8); }']
        expected += [str(1 << 127), str((1 << 64)-1), '2', str(1 << 64), str(MASK), str((1 << 64)-1), 'false', '7']
        source = root/'scalar.goose'
        source.write_text('\n'.join(declarations) + '\nfn main() {\n' + '\n'.join(calls) + '\n}\n')
        run([goose, '--check', '--roundtrip', source]); checks += 1
        for cc in [os.environ.get('CC', 'gcc'), os.environ.get('CLANG', 'clang')]:
            assert shutil.which(cc), f'{cc} required for native acceptance'
            for opt in [0, 2]:
                binary = root/f'scalar-{pathlib.Path(cc).name}-{opt}'
                run([goose, 'build', '--cc', cc, f'-O{opt}', source, '-o', binary])
                actual = run([binary]).splitlines()
                assert actual == expected, (cc, opt, [(a,b) for a,b in zip(actual,expected) if a != b][:10], actual[-10:])
                checks += len(expected)
        for i, body in enumerate([
            'let x: u64 = 18446744073709551616;',
            'let x: u128 = -1;',
            'let x = 340282366920938463463374607431768211456;',
            'var x: u128 = 0; unsafe_atomic_load<u128>(0, "Relaxed");',
        ]):
            bad = root/f'bad{i}.goose'; bad.write_text('fn main() {' + body + '}')
            run([goose, '--check', bad], expected=1); checks += 1
    print(f'u128 native: {checks} checks passed')

if __name__ == '__main__':
    main()
