#!/usr/bin/env python3
"""Differential tests for the direct scalar Wasm backend; no generated-C Wasm path."""
import argparse
import random
import math
import struct
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(command, *, ok=True):
    result = subprocess.run([str(c) for c in command], cwd=ROOT, capture_output=True, timeout=90)
    if ok and result.returncode:
        raise AssertionError(f"command failed ({result.returncode}): {' '.join(map(str, command))}\n"
                             f"stdout:\n{result.stdout.decode(errors='replace')}\n"
                             f"stderr:\n{result.stderr.decode(errors='replace')}")
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe', type=Path, default=ROOT / 'build' / 'goose')
    p.add_argument('--node', default='node')
    p.add_argument('--validator', default='wasm-tools')
    p.add_argument('--cc', default='cc')
    p.add_argument('--cxx', default='c++')
    p.add_argument('--wasmtime-python', type=Path, help='Python with optional wasmtime==49.0.0')
    args = p.parse_args()
    exe = args.exe.resolve()
    for command in (args.node, args.validator, args.cc, args.cxx):
        if not shutil.which(command):
            p.error(f'required executable is missing: {command}')
        run([command, '--version'])  # Check broken version-manager shims too.
    out = ROOT / 'build' / 'gen' / 'wasm'
    out.mkdir(parents=True, exist_ok=True)
    count = 0
    sources = sorted((ROOT / 'test' / 'wasm').glob('*.goose'))
    sources.extend(ROOT / 'test' / 'typing' / f'{name}.goose' for name in (
        'global_optional_flow', 'optional_loop_callee_assignments',
        'optional_while_condition_calls', 'u64_cmp_readonly_refs',
    ))
    for source in sources:
        expected = (ROOT / 'test' / 'expected' / (source.stem + '.out')).read_bytes()
        for opt in (0, 2):
            prefix = out / f'{source.stem}-O{opt}'
            c = prefix.with_suffix('.c')
            native = prefix.with_suffix('.native')
            wasm = prefix.with_suffix('.wasm')
            run([exe, f'-O{opt}', '--standalone', '-o', c, source])
            run([args.cc, f'-O{opt}', c, '-pthread', '-lm', '-ldl', '-o', native])
            reference = run([native])
            assert reference.stdout == expected, (source, opt, 'native fixture expectation')
            run([exe, f'-O{opt}', '--target', 'wasm', '-o', wasm, source])
            assert wasm.read_bytes()[:8] == b'\0asm\x01\0\0\0', 'invalid binary magic/version'
            run([args.validator, 'validate', wasm])
            actual = run([args.node, ROOT / 'scripts' / 'run_wasm.mjs', wasm])
            assert actual.stdout == reference.stdout, (source, opt, actual.stdout, reference.stdout)
            assert not actual.stderr, (source, opt, actual.stderr)
            if args.wasmtime_python:
                second = run([args.wasmtime_python, ROOT / 'test' / 'wasmtime_host.py', wasm])
                assert second.stdout == reference.stdout and not second.stderr, (source, opt, second.stdout, second.stderr)
                count += 1
            if source.stem == 'wasm_tail_values':
                resource = run([args.node, ROOT / 'test' / 'wasm_runtime.mjs', wasm, 'print'])
                assert resource.stdout == reference.stdout, 'print owner check changed output'
                count += 1
            count += 1
    growth_source = out / 'frame-growth.goose'
    lines = ['recursive fn grow(n: i64) -> i64 {']
    for i in range(96):
        lines += [f'var a{i}: i64 = 1;', f'let r{i} = &a{i};']
    lines += ['if n > 0 { a0 += grow(n - 1); }',
              'return ' + ' + '.join(f'r{i}' for i in range(96)) + ';',
              '}', 'fn main() { print(grow(100)); }']
    growth_source.write_text('\n'.join(lines) + '\n')
    for opt in (0, 2):
        wasm = out / f'frame-growth-O{opt}.wasm'
        run([exe, f'-O{opt}', '--target', 'wasm', '-o', wasm, growth_source])
        run([args.validator, 'validate', wasm])
        result = run([args.node, ROOT / 'test' / 'wasm_runtime.mjs', wasm, 'growth'])
        assert result.stdout == b'9696\n'
        count += 1
        if args.wasmtime_python:
            assert run([args.wasmtime_python, ROOT / 'test' / 'wasmtime_host.py', wasm]).stdout == result.stdout
            count += 1
        # Set Memory 0's maximum to its initial page count. This changes only
        # the test module's resource limit and makes memory.grow fail for real.
        def leb(data, pos):
            value, shift = 0, 0
            while True:
                byte = data[pos]
                pos += 1
                value |= (byte & 127) << shift
                if not byte & 128:
                    return value, pos
                shift += 7
        original = wasm.read_bytes()
        cursor = 8
        sections = bytearray(original[:8])
        while cursor < len(original):
            start = cursor
            ident = original[cursor]
            length, body = leb(original, cursor + 1)
            cursor = body + length
            if ident == 5:
                assert original[body:body + 3] == b'\x01\x01\x01', 'expected one Memory32 with minimum one page'
                sections += b'\x05\x04\x01\x01\x01\x01'
            else:
                sections += original[start:cursor]
        limited = out / f'frame-growth-limited-O{opt}.wasm'
        limited.write_bytes(sections)
        run([args.validator, 'validate', limited])
        run([args.node, ROOT / 'test' / 'wasm_runtime.mjs', limited, 'growth-failure'])
        count += 1
    # Deterministic values exercise arithmetic at each declared storage width,
    # independent of constant folding and of the receiving slot's width.
    randomizer = random.Random(20261106)
    lines = ['fn main() {']
    for width in (8, 16, 32, 64):
        for unsigned in (False, True):
            typ = ('u' if unsigned else 'i') + str(width)
            low, high = (0, 2**width - 1) if unsigned else (-2**(width-1), 2**(width-1)-1)
            for sample in range(12):
                a, b = randomizer.randint(low, high), randomizer.randint(low, high) or 1
                lines += ['{', f'var a: {typ} = {a};', f'var b: {typ} = {b};', f'var shift = {sample * 7};']
                for operator in ('+', '-', '*', '/', '%', '&', '|', '^'):
                    lines.append(f'print(a {operator} b);')
                lines += ['print(a << shift, ",", a >> shift);',
                          'print(a < b, a <= b, a > b, a >= b, a == b, a != b);', '}']
    for width, encoding in ((32, 'f'), (64, 'd')):
        for sample in range(40):
            while True:
                bits = randomizer.getrandbits(width)
                value = struct.unpack('<' + encoding, bits.to_bytes(width // 8, 'little'))[0]
                if math.isfinite(value):
                    break
            literal = repr(value)
            lines += ['{', f'var f: f{width} = {literal};', 'print(f);', '}']
    lines += ['}']
    numeric = out / 'numeric.goose'
    numeric.write_text('\n'.join(lines) + '\n')
    for opt in (0, 2):
        c, native, wasm = out / f'numeric-O{opt}.c', out / f'numeric-O{opt}.native', out / f'numeric-O{opt}.wasm'
        run([exe, f'-O{opt}', '--standalone', '-o', c, numeric])
        run([args.cc, f'-O{opt}', c, '-pthread', '-lm', '-ldl', '-o', native])
        reference = run([native])
        run([exe, f'-O{opt}', '--target', 'wasm', '-o', wasm, numeric])
        run([args.validator, 'validate', wasm])
        assert run([args.node, ROOT / 'scripts' / 'run_wasm.mjs', wasm]).stdout == reference.stdout, ('numeric', opt)
        count += 1
        if args.wasmtime_python:
            assert run([args.wasmtime_python, ROOT / 'test' / 'wasmtime_host.py', wasm]).stdout == reference.stdout, ('numeric Wasmtime', opt)
            count += 1
    # Exercise the binary encoder itself with true multi-memory memargs and
    # signed LEB boundary values, independent of Goose storage lowering.
    binary_test, binary_module = out / 'wasm-binary-test', out / 'encoder.wasm'
    run([args.cxx, '-std=c++20', '-O0', ROOT / 'test' / 'wasm_binary.cpp', '-o', binary_test])
    overflow = run([binary_test, 'overflow'], ok=False)
    if overflow.returncode == 77:
        print('skip valid >4GiB span check: this host cannot provide its bounded virtual mapping')
    else:
        assert not overflow.returncode, overflow.stderr
        count += 1
    run([binary_test, binary_module])
    run([args.validator, 'validate', binary_module])
    js = """const fs=require('node:fs'), a=require('node:assert/strict');
const x=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[1]))).exports;
const values=[0n,63n,64n,127n,128n,-64n,-65n,-128n,-129n,-9223372036854775808n,9223372036854775807n];
values.forEach((v,i)=>a.equal(x['constant'+i](),v)); a.equal(x.unaligned(),values[9]);
a.equal(new DataView(x.other.buffer).getBigInt64(1,true),values[9]);
a.equal(new DataView(x.memory.buffer).getBigInt64(1,true),0n);"""
    run([args.node, '-e', js, binary_module])
    count += 1
    bounded = out / 'bounded-conversion.goose'
    bounded.write_text("""fn main() {
    var value = -3.75;
    for i in 8 {
        assert((value as! i64) == i / 2 - 3);
        value += 0.5;
    }
    var single: f32 = -3.75;
    for i in 8 {
        assert((single as! i16) == i / 2 - 3);
        single += 0.5;
    }
    var unsigned_value = 300.5;
    assert((unsigned_value as! u8) == 44);
    assert((unsigned_value as! u64) == 300);
    var negative = -3.75;
    assert((negative as! u64) == 18446744073709551613);
    var lower = -9223372036854775808.0;
    assert((lower as! i64) == -9223372036854775808);
    var upper = 9223372036854774784.0;
    assert((upper as! i64) == 9223372036854774784);
}\n""")
    for opt in (0, 2):
        wasm = out / f'bounded-conversion-O{opt}.wasm'
        c, native = out / f'bounded-conversion-O{opt}.c', out / f'bounded-conversion-O{opt}.native'
        run([exe, f'-O{opt}', '--standalone', '-o', c, bounded])
        run([args.cc, f'-O{opt}', c, '-pthread', '-lm', '-ldl', '-o', native])
        assert run([native]).stdout == b''
        run([exe, f'-O{opt}', '--target', 'wasm', '-o', wasm, bounded])
        run([args.validator, 'validate', wasm])
        run([args.node, ROOT / 'test' / 'wasm_conversion.mjs', wasm])
        count += 1
        if args.wasmtime_python:
            assert run([args.wasmtime_python, ROOT / 'test' / 'wasmtime_host.py', wasm]).stdout == b''
            count += 1
    # Known runtime failures must occur for the same operation, not just any trap.
    failures = [
        ('assert', 'assert(false);', b'assert failed'),
        ('zero', 'var n = 0; print(7 / n);', b'division by zero'),
        ('divoverflow', 'var n = -9223372036854775808; var m = -1; print(n / m);', b'overflow'),
    ]
    for name, body, reason in failures:
        source = out / f'failure-{name}.goose'
        source.write_text('fn main() { ' + body + ' }\n')
        for opt in (0, 2):
            wasm = out / f'failure-{name}-O{opt}.wasm'
            native = out / f'failure-{name}-O{opt}.native'
            c = native.with_suffix('.c')
            run([exe, f'-O{opt}', '--standalone', '-o', c, source])
            run([args.cc, c, '-pthread', '-lm', '-ldl', '-o', native])
            ref = run([native], ok=False)
            run([exe, f'-O{opt}', '--target', 'wasm', '-o', wasm, source])
            run([args.validator, 'validate', wasm])
            actual = run([args.node, ROOT / 'scripts' / 'run_wasm.mjs', wasm], ok=False)
            assert ref.returncode and actual.returncode, (name, opt, 'missing failure')
            assert reason in ref.stderr and reason in actual.stderr, (name, ref.stderr, actual.stderr)
            assert ref.stdout == actual.stdout == b'', (name, 'partial print leaked')
            if args.wasmtime_python:
                second = run([args.wasmtime_python, ROOT / 'test' / 'wasmtime_host.py', wasm], ok=False)
                assert second.returncode and reason in second.stderr and not second.stdout, (name, opt, second.stderr)
                count += 1
            count += 1
    # No stubs, no native extern reinterpretation, and no partial output on error.
    unsupported = [
        ('array', 'fn main() { var a = [1, 2]; print(a); }', b'layout'),
        ('export', 'export fn twice(x: i64) -> i64 { return x * 2; } fn main() {}', b'export'),
        ('extern', 'extern fn abs(x: i64) -> i64; fn main() { print(abs(-7)); }', b'extern'),
        ('nonlocal', 'fn a() -> i64 { return b(); } fn b() -> i64 { return 7 from a; } fn main() { print(a()); }', b'nonlocal'),
    ]
    for name, text, reason in unsupported:
        source, wasm = out / f'unsupported-{name}.goose', out / f'unsupported-{name}.wasm'
        source.write_text(text + '\n')
        wasm.unlink(missing_ok=True)
        result = run([exe, '-O0', '--target', 'wasm', '-o', wasm, source], ok=False)
        assert result.returncode and b'wasm target:' in result.stderr and reason in result.stderr, (name, result.stderr)
        assert not wasm.exists(), (name, 'partial module')
        if name == 'nonlocal':
            run([exe, '-O2', '--target', 'wasm', '-o', wasm, source])
            run([args.validator, 'validate', wasm])
            assert run([args.node, ROOT / 'scripts' / 'run_wasm.mjs', wasm]).stdout == b'7\n'
            text = run([args.validator, 'print', wasm]).stdout
            assert b'(tag ' not in text and b'throw ' not in text, 'inlined return uses exceptions'
            count += 1
        count += 1
    fixture = ROOT / 'test' / 'wasm' / 'wasm_scalars.goose'
    for flags in (['--target'], ['--target', 'other'], ['--target', 'wasm', '--jit'],
                  ['run', '--target', 'wasm'], ['--target', 'wasm', '--debug']):
        result = run([exe, *flags, fixture], ok=False)
        assert result.returncode, flags
        count += 1
    # Percent substitution must finish before checking source/output identity.
    preserved = out / 'preserved.goose'
    original = b'fn main() { print(1); }\n'
    preserved.write_bytes(original)
    result = run([exe, '--target', 'wasm', '--multi-test', '-o', out / '%.goose', preserved], ok=False)
    assert b'must not overwrite' in result.stderr and b'--multi-test: exit 1' in result.stderr, result.stderr
    assert preserved.read_bytes() == original, 'source overwritten after percent expansion'
    count += 1
    # The build verb and flag form must emit exactly the same module bytes.
    flag, verb = out / 'flag.wasm', out / 'verb.wasm'
    run([exe, '--target', 'wasm', '-o', flag, fixture])
    run([exe, 'build', '--target', 'wasm', '-o', verb, fixture])
    assert flag.read_bytes() == verb.read_bytes()
    print(f'wasm backend: {count + 1} checks passed')


if __name__ == '__main__':
    main()
