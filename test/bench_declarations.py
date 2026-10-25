#!/usr/bin/env python3
"""Declaration discovery acceptance tests; never execute a benchmark body."""
import pathlib
import subprocess
import sys
import tempfile

exe = pathlib.Path(sys.argv[1]).resolve()
checks = 0


def invoke(*args, ok=True, contains=None):
    global checks
    result = subprocess.run([str(exe), *map(str, args)], text=True, capture_output=True)
    assert (result.returncode == 0) == ok, (args, result.stdout, result.stderr)
    if contains:
        assert contains in result.stdout + result.stderr, (args, contains, result.stdout, result.stderr)
    if args[0] == "bench":
        assert result.returncode == (0 if ok else 2), (args, result.returncode, result.stderr)
    checks += 1
    return result


with tempfile.TemporaryDirectory(prefix="goose-bench-declarations-") as directory:
    root = pathlib.Path(directory)
    source = root / "entry.goose"
    imported = root / "helper.goose"
    imported.write_text('bench "imported" fn helper::other() -> i64 { 4 }\n')
    source.write_text('import .helper;\n'
                      'fn initialize() -> i64 { abort("listing ran setup"); }\nlet setup = initialize();\n'
                      '/// Entry documentation.\n'
                      'bench "line\\n\\\"quoted\\\"\\t\\x1b" fn ns::first() { 1 }\n'
                      'bench "same" fn second() -> i64, bool { return 2, true; }\n')
    result = invoke("bench", source, "--list")
    lines = result.stdout.splitlines()
    assert len(lines) == 2 and lines[0].startswith('ns::first\t"line\\n\\\"quoted\\\"\\t\\u001b"\tmedium\t')
    assert lines[1] == 'second\t"same"\tmedium\t() -> i64, bool'
    result = invoke("bench", source, "--list", "--filter", "second", "--sizes", "large,small")
    assert [line.split('\t')[2] for line in result.stdout.splitlines()] == ["small", "large"]
    invoke("bench", source, "--list", "--filter", "same", ok=False, contains="unknown benchmark key")
    invoke("bench", source, "--list", "--filter", "helper::other", ok=False, contains="unknown benchmark key")
    for sizes in ("", "small,small", "SMALL", "small,", ",small"):
        invoke("bench", source, "--list", "--sizes", sizes, ok=False)
    invoke("bench", source, "--list", "--define", 'BENCH_SIZE="small"', ok=False, contains="duplicate")
    invoke("bench", source, "--samples", "4", ok=False, contains="samples >= 5")
    invoke("bench", source, "--list", "--jit", ok=False)
    invoke("check", source, "--roundtrip")
    dumped = invoke("--dump", source).stdout
    assert 'bench "line\\n' in dumped and 'fn ns::first' in dumped
    assert 'fn ns::first' in invoke("--dump-docs", source).stdout
    # Filtered-out entries and imported declarations must still be validated.
    source.write_text('bench "good" fn good() { 1 }\nbench "bad" fn bad() { missing_name }\n')
    invoke("bench", source, "--list", "--filter", "good", ok=False, contains="missing_name")
    source.write_text('import .helper; bench "good" fn good() { 1 }\n')
    imported.write_text('bench "bad" fn other(x: i64) { x }\n')
    invoke("bench", source, "--list", ok=False, contains="bench function takes no parameters")
    source.write_text('bench "configured" fn configured() { build::BENCH_SIZE }\n')
    invoke("bench", source, "--list", ok=False, contains="bench results must")
    source.write_text('bench "configured" fn configured() { if build::BENCH_SIZE == "small" { 1 } else { 2 } }\n')
    invoke("bench", source, "--list", "--sizes", "large,medium,small", contains="small")
    invoke("check", source, ok=False, contains="BENCH_SIZE")
    invoke("check", source, "--define", 'BENCH_SIZE="medium"', "--roundtrip")
    invoke("build", source, "--define", 'BENCH_SIZE="medium"', ok=False, contains="main")
    invoke("run", source, "--define", 'BENCH_SIZE="medium"', ok=False, contains="main")
    source.write_text('bench "\\x7f\\xc2\\x9b" fn controls() { 1 }\n')
    result = invoke("bench", source, "--list")
    assert result.stdout == 'controls\t"\\u007f\\u009b"\tmedium\t() -> i64\n', result.stdout
    source.write_text('fn main() {}\n')
    invoke("bench", source, "--list", ok=False, contains="no benchmarks declared")
print(f"benchmark declarations: {checks} checks passed")
