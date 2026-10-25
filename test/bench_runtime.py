#!/usr/bin/env python3
"""Native bench mechanics. Sleeps only establish a loose setup/call boundary."""
import pathlib
import re
import platform
import shutil
import signal
import time
import subprocess
import sys
import tempfile

exe = pathlib.Path(sys.argv[1]).resolve()
checks = 0


def invoke(source, *options, code=0, contains=None):
    global checks
    result = subprocess.run([str(exe), 'bench', str(source), *options], capture_output=True, text=True, timeout=120)
    assert result.returncode == code, (result.args, result.returncode, result.stdout, result.stderr)
    if contains:
        assert contains in result.stdout + result.stderr, (contains, result.stdout, result.stderr)
    checks += 1
    return result


def artifacts(result):
    return pathlib.Path(re.search(r'benchmark artifacts: (.+)', result.stderr)[1])


def attempts(result):
    return [line.split('\t') for line in result.stdout.splitlines()]


if sys.platform != 'linux':
    print('benchmark runtime: Linux execution only (skipped)')
    sys.exit(0)

with tempfile.TemporaryDirectory(prefix='goose-bench-runtime-test-') as directory:
    source = pathlib.Path(directory) / 'entry.goose'
    source.write_text('import std;\n'
                      'fn initialize() -> i64 { print("SETUP"); 42 }\n'
                      'let fixture = initialize();\n'
                      'bench "same" fn ns::selected() -> i64 { print("CALL"); fixture }\n'
                      'bench "same" fn other() -> i64 { abort("unselected"); }\n'
                      'fn main() { abort("main ran"); }\n')
    for mode, children in [('reuse', 1), ('process', 9)]:
        result = invoke(source, '--isolation', mode, '--filter', 'ns::selected')
        rows = attempts(result)
        assert len(rows) == 9 and [r[2] for r in rows] == ['warmup'] * 2 + ['measure'] * 7
        assert all(r[0] == 'ns::selected' and r[-1] == 'i64:42;' for r in rows)
        logs = list(artifacts(result).glob('*.stdout'))
        assert len(logs) == children
        text = ''.join(p.read_text() for p in logs)
        assert text.count('SETUP') == children and text.count('CALL') == 9
        checks += 1
    invoke(source, '--filter', 'same', code=2, contains='unknown benchmark key')
    invoke(source, '--filter', 'ns::selected', '--sizes', 'small,large', '--samples', '5', '--warmups', '1')
    # No child or checksum baseline is shared between different keys or sizes.
    source.write_text('extern fn process_id() -> i32 = "getpid";\nlet pid = process_id();\n'
                      'bench "a" fn a() -> i32 { pid }\nbench "b" fn b() -> i32 { pid }\n')
    result = invoke(source, '--sizes', 'small,large', '--samples', '5', '--warmups', '1')
    rows = attempts(result)
    groups = {(r[0], r[1]): {x[-1] for x in rows if x[:2] == r[:2]} for r in rows}
    assert len(rows) == 24 and len(groups) == 4 and all(len(values) == 1 for values in groups.values())
    assert len(set().union(*groups.values())) == 4
    checks += 1
    # Native and Goose debug/unoptimized controls retain exactly one call per sample.
    result = invoke(source, '--filter', 'a', '-O0', '--debug', '--samples', '5', '--warmups', '1')
    assert len(attempts(result)) == 6
    checks += 1
    # Global mutable state is deliberately destructive: process mode resets it.
    source.write_text('var counter: i64 = 0;\n'
                      'bench "state" fn state() -> i64 { counter += 1; counter }\n')
    invoke(source, code=1, contains='checksum disagreement')  # disagreement during warmup
    result = invoke(source, '--isolation', 'process', '--samples', '5', '--warmups', '1')
    assert len(attempts(result)) == 6 and all(r[-1] == 'i64:1;' for r in attempts(result))
    # Agreement in warmup is insufficient: measured calls are compared too.
    source.write_text('var counter: i64 = 0;\n'
                      'bench "state" fn state() -> i64 { counter += 1; if counter <= 2 { 1 } else { 2 } }\n')
    invoke(source, code=1, contains='checksum disagreement')
    source.write_text('bench "bits" fn bits() -> i8, u8, i16, u16, i32, u32, i64, u64, bool, f32, f64 {\n'
                      'return -128, 255, -32768, 65535, -2147483648, 4294967295, -9223372036854775808, 18446744073709551615, true, 1.5, -0.0; }\n')
    result = invoke(source, '--samples', '5', '--warmups', '1')
    assert 'u64:18446744073709551615;' in result.stdout and 'f32:0x3fc00000;' in result.stdout and 'f64:0x8000000000000000;' in result.stdout
    checks += 1
    source.write_text('var zero: f64 = 0.0;\nbench "nan" fn nan() -> f64 { zero / zero }\n')
    invoke(source, code=1, contains='nonfinite benchmark checksum')
    source.write_text('var count: i64 = 0;\nbench "zero bits" fn bits() -> f64 { count += 1; if count == 1 { 0.0 } else { -0.0 } }\n')
    invoke(source, code=1, contains='checksum disagreement')
    source.write_text('bench "crash" fn crash() -> i64 { abort("body failed"); }\n')
    invoke(source, code=1, contains='sample failed')
    # All variants must compile before any initializer or benchmark executes.
    marker = pathlib.Path(directory) / 'setup-marker'
    source.write_text('import os;\nfn initialize() -> i64 { append_file("' + str(marker) + '", "setup"); 1 }\nlet fixture = initialize();\n'
                      'bench "build all" fn entry() -> i64 {\nconst if build::BENCH_SIZE == "large" { missing_name } else { fixture } }\n')
    invoke(source, '--sizes', 'small,large', code=2, contains='missing_name')
    assert not marker.exists()
    checks += 1
    # An untimed 400 ms initializer must not leak into a tiny timed call.
    source.write_text('import os;\nfn initialize() -> i64 { sleep_ms(400); 7 }\nlet fixture = initialize();\n'
                      'bench "setup" fn entry() -> i64 { fixture }\n')
    for mode in ('reuse', 'process'):
        result = invoke(source, '--isolation', mode, '--samples', '5', '--warmups', '1')
        assert max(int(r[4].split()[0]) for r in attempts(result)) < 200_000_000, result.stdout
        checks += 1
    # Large output is drained and bounded; stdout cannot fake control messages.
    source.write_text('import os;\nbench "noisy" fn noisy() -> i64 {\n'
                      'for i in 300 { write_stdout("' + 'x' * 8192 + '"); } 1 }\n')
    result = invoke(source, '--samples', '5', '--warmups', '1')
    logs = list(artifacts(result).glob('*.stdout'))
    assert len(logs) == 1 and logs[0].stat().st_size == 1048576 and 'truncated' in result.stderr
    checks += 1
    # Parent cancellation cleans up the workload process group during setup.
    source.write_text('import os;\nfn setup() -> i64 { sleep_ms(30000); 1 }\nlet fixture = setup();\n'
                      'bench "interrupt" fn entry() -> i64 { fixture }\n')
    with tempfile.TemporaryFile(mode='w+') as diagnostics:
        process = subprocess.Popen([str(exe), 'bench', str(source)], stdout=subprocess.PIPE, stderr=diagnostics, text=True)
        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                diagnostics.seek(0)
                text = diagnostics.read()
                found = re.search(r'benchmark artifacts: (.+)', text)
                if found and list(pathlib.Path(found[1]).glob('*.stdout')):
                    break
                time.sleep(.02)
            else:
                raise AssertionError('child did not reach setup: ' + text)
            process.send_signal(signal.SIGINT)
            process.communicate(timeout=10)
            assert process.returncode == 130, (process.returncode, text)
            checks += 1
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
    # Local data stacks are restored on every call (including multiple returns).
    source.write_text('bench "locals" fn locals() -> i64, i64 {\n'
                      'var data: i64[>..] = []; for i in 1000 { data.push(i); } return data.len, data[999]; }\n')
    result = invoke(source, '--samples', '5', '--warmups', '1')
    assert all(r[-1] == 'i64:1000;i64:999;' for r in attempts(result))
    checks += 1
    # Regression guard on the actual optimized opaque timer, independent of
    # workload optimization. x86-64 GCC/Clang must retain one indirect call
    # between the two clock reads, and result encoding after the stop read.
    if platform.machine() == 'x86_64' and shutil.which('objdump'):
        obj = artifacts(result) / 'medium' / 'runner.o'
        assembly = subprocess.check_output(['objdump', '-dr', str(obj)], text=True)
        clocks = list(re.finditer(r'R_X86_64_\w+\s+clock_gettime', assembly))
        assert len(clocks) == 2, assembly
        between = assembly[clocks[0].end():clocks[1].start()]
        assert len(re.findall(r'call\s+\*', between)) == 1, between
        assert assembly.index('open_memstream') > clocks[1].end()
        checks += 1

print(f'benchmark runtime: {checks} checks passed')
