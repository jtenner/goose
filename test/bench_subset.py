#!/usr/bin/env python3
"""Black-box subset-compiler checks derived from the benchmark spec."""
import pathlib
import subprocess
import sys
import tempfile

exe = pathlib.Path(sys.argv[1]).resolve()
checks = 0
with tempfile.TemporaryDirectory(prefix="goose-subset-bench-") as directory:
    root = pathlib.Path(directory)
    source = root / "entry.goose"

    def check(text, expected=None, mode="--check"):
        global checks
        source.write_text(text)
        result = subprocess.run([str(exe), mode, str(source)], text=True, capture_output=True)
        assert (result.returncode == 0) == (expected is None), (text, result.stdout, result.stderr)
        if expected:
            assert expected in result.stderr, (text, expected, result.stderr)
        checks += 1

    check('bench "line\\n\\\"quoted\\\"" fn ns::entry() -> i64 { 4 }')
    check('bench "same" fn first() { 1 } bench "same" fn second() -> bool { true }')
    check('fn bench() -> i64 { 1 } fn main() { bench(); }')
    check('bench "" fn f() { 1 }', 'bench label must be nonempty')
    check('fn main() { bench "nested" fn f() { 1 } }', 'bench requires a top-level function')
    check('bench "x" recursive fn f() { 1 }', 'bench requires an unmodified fn declaration')
    check('bench "x" fn f(x: i64) { x }', 'bench function takes no parameters')
    check('bench "x" fn f<T>() { 1 }', 'bench function cannot be generic')
    check('bench "x" fn f() { 1 } fn f(x: i64) { x }', 'bench key cannot share an overload set')
    check('bench "x" fn main() {}', 'bench key cannot be main')
    check('bench "x" fn f() {}', 'bench results must')
    check('bench "x" fn f() { "string" }', 'bench results must')
    check('bench "x" fn f() { absent }', 'unknown')
    check('bench "x" fn f() -> i64, bool { return 1, true; }', 'not implemented yet: multiple return values')
    # Emission retains the ordinary requirement for a main entry.
    source.write_text('bench "x" fn f() { 1 } fn main() { f(); }')
    output = root / "entry.c"
    result = subprocess.run([str(exe), '-o', str(output), str(source)], text=True, capture_output=True)
    assert result.returncode == 0 and output.stat().st_size, result.stderr
    result = subprocess.run([str(exe), 'bench', str(source)], text=True, capture_output=True)
    assert result.returncode != 0 and 'not implemented' in result.stderr, result.stderr
    checks += 2
print(f"subset benchmark declarations: {checks} checks passed")
