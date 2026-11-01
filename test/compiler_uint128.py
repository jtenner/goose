#!/usr/bin/env python3
"""Independent portable constant arithmetic against Python big integers."""
import pathlib
import random
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
MASK = (1 << 128) - 1

def main():
    rng = random.Random(0x128)
    values = [0, 1, (1 << 64)-1, 1 << 64, (1 << 127)-1, 1 << 127, MASK]
    values += [rng.getrandbits(128) for _ in range(128)]
    checks = []
    def u(n):
        return f'UInt128({n & ((1 << 64)-1)}ULL, {n >> 64}ULL)'
    for a in values:
        for b in values[:7] + [rng.getrandbits(128)]:
            for op, result in [('+', a+b), ('-', a-b), ('*', a*b),
                               ('&', a&b), ('|', a|b), ('^', a^b)]:
                checks.append(f'CHECK(({u(a)} {op} {u(b)}) == {u(result & MASK)});')
            if b:
                for op, result in [('/', a//b), ('%', a%b)]:
                    checks.append(f'CHECK(({u(a)} {op} {u(b)}) == {u(result)});')
            checks.append(f'CHECK(({u(a)} < {u(b)}) == {str(a < b).lower()});')
        for n in [0, 1, 63, 64, 65, 127, 128, 129]:
            checks.append(f'CHECK(({u(a)} << {n}) == {u((a << n) & MASK)});')
            checks.append(f'CHECK(({u(a)} >> {n}) == {u(a >> n)});')
        checks.append(f'CHECK({u(a)}.Decimal() == "{a}");')
        checks.append(f'CHECK(UInt128::Parse("{a}", 10, v) && v == {u(a)});')
        checks.append(f'CHECK(UInt128::Parse("{a:x}", 16, v) && v == {u(a)});')
    checks += [f'CHECK(!UInt128::Parse("{1 << 128}", 10, v));',
               'CHECK(!UInt128::Parse("100000000000000000000000000000000", 16, v));']
    with tempfile.TemporaryDirectory(prefix='goose-u128-') as directory:
        d = pathlib.Path(directory)
        source = '#include "src/uint128.h"\n#include <cstdio>\nusing goose::UInt128;\n'
        source += '#define CHECK(x) if (!(x)) { fprintf(stderr, "line %d\\n", __LINE__); return 1; }\n'
        source += 'int main() { UInt128 v;\n' + '\n'.join(checks) + '\n}\n'
        (d/'test.cpp').write_text(source)
        subprocess.run(['c++', '-std=c++20', '-O0', '-fsanitize=undefined',
                        '-I', str(ROOT), str(d/'test.cpp'), '-o', str(d/'test')], check=True)
        subprocess.run([str(d/'test')], check=True)
    print(f'portable u128: {len(checks)} checks passed (Python oracle, UBSan)')

if __name__ == '__main__':
    main()
