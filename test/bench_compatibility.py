#!/usr/bin/env python3
"""Benchmark codegen roots and ordinary commands; no timing assertions."""
import json
import pathlib
import subprocess
import sys
import tempfile

exe = pathlib.Path(sys.argv[1]).resolve()
checks = 0


def invoke(*args, ok=True, contains=None):
    global checks
    result = subprocess.run([str(exe), *map(str, args)], text=True,
                            capture_output=True, timeout=120)
    assert (result.returncode == 0) == ok, (args, result.stdout, result.stderr)
    if contains:
        assert contains in result.stdout + result.stderr, (args, result.stdout, result.stderr)
    checks += 1
    return result


with tempfile.TemporaryDirectory(prefix="goose-bench-compatibility-") as directory:
    root = pathlib.Path(directory)
    source = root / "entry.goose"
    generated = root / "entry.c"
    declarations = ('thread_fn worker() {}\n'
                    'bench "threaded" fn threaded() -> bool { thread_wait(thread_spawn(worker)) }\n'
                    'bench "value" fn value() -> i64 { 42 }\n')
    for level in ("-O0", "-O2"):
        source.write_text(declarations + 'fn main() { print("ordinary"); }\n')
        invoke("check", level, source)
        result = invoke("run", level, source)
        assert result.stdout == "ordinary\n", result.stdout
        invoke(level, source, "-o", generated)
        assert "#define GS_NEED_THREADS 1" not in generated.read_text()
        # An ordinary call still reaches the annotated body.
        source.write_text(declarations + 'fn main() { print(value()); }\n')
        result = invoke("run", level, source)
        assert result.stdout == "42\n", result.stdout
        source.write_text(declarations + 'fn main() { print(threaded()); }\n')
        invoke("run", level, source, ok=False, contains="JIT mode does not support threads")
        # The bench command must retain bodies that main does not call.
        if sys.platform.startswith("linux"):
            source.write_text(declarations + 'fn main() { abort("main ran"); }\n')
            listing = root / "listing.json"
            invoke("bench", level, source, "--list", "--json", listing)
            assert [row["key"] for row in json.loads(listing.read_text())["results"]] == ["threaded", "value"]
            report = root / "result.json"
            invoke("bench", level, source, "--temperature", "off", "--samples", "5",
                   "--warmups", "1", "--json", report)
            rows = json.loads(report.read_text())["results"]
            assert [row["key"] for row in rows] == ["threaded", "value"]
            for row, expected in zip(rows, (("bool", True), ("i64", "42"))):
                assert len(row["attempts"]) == 6, row
                assert all([(c["type"], c["value"]) for c in attempt["checksum"]["components"]] == [expected]
                           for attempt in row["attempts"]), row
    # Removing codegen roots must not skip semantic validation.
    source.write_text('bench "bad" fn bad() { missing_name }\nfn main() {}\n')
    for command in ("check", "run", "build"):
        invoke(command, source, ok=False, contains="missing_name")

print(f"benchmark compatibility: {checks} checks passed")
