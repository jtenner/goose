#!/usr/bin/env python3
"""Standalone unsafe pointer regression matrix, including full alignment UBSan.

Run after building Goose: python3 test/unsafe_pointer.py --exe build/goose.
Uses real libc malloc/free declarations in the Goose fixture, not C adapters.
Artifacts are retained under build/gen/unsafe-pointer for review.
"""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=ROOT / "build/goose")
    args = parser.parse_args()
    goose = args.exe.resolve()
    out = ROOT / "build/gen/unsafe-pointer"
    out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, GOOSE_HOME=str(ROOT / "build/unsafe-home"))
    # LeakSanitizer also verifies the test's libc object is actually freed.
    env["ASAN_OPTIONS"] = "detect_leaks=1"
    checks = 0

    def run(argv, error=None, output=None):
        nonlocal checks
        result = subprocess.run([str(x) for x in argv], cwd=ROOT, env=env,
                                capture_output=True, text=True, timeout=120)
        text = result.stdout + result.stderr
        if error is not None:
            assert result.returncode != 0 and error in text, (argv, result.returncode, text)
        else:
            assert result.returncode == 0, (argv, result.returncode, text)
        if output is not None:
            assert result.stdout.strip() == output, (argv, text)
        checks += 1
        return text

    fixture = ROOT / "test/memory/unsafe_pointer.goose"
    run([goose, "--roundtrip", "--check", fixture])
    for fixture_error in sorted((ROOT / "test/errors_tc").glob("unsafe_pointer_*.goose")):
        marker = re.search(r"^// error: (.+)$", fixture_error.read_text(), re.M)[1]
        run([goose, "--check", fixture_error], error=marker)

    compilers = []
    for name in ("gcc", "clang"):
        compiler = shutil.which(name)
        assert compiler, f"{name} is required for this matrix"
        compilers.append((name, compiler))

    errors = {
        "null_load": ('unsafe_load<u8>(unsafe_ptr_from_handle(0), false);', "unsafe pointer is null"),
        "null_store": ('unsafe_store<u64>(default<UnsafePtr>(), 1, false);', "unsafe pointer is null"),
        "null_add": ('unsafe_ptr_add(unsafe_ptr_from_handle(0), 0);', "unsafe pointer is null"),
        "overflow": ('unsafe_ptr_add(unsafe_ptr_from_handle(18446744073709551615), 1);', "unsafe pointer address overflow"),
        "underflow": ('unsafe_ptr_add(unsafe_ptr_from_handle(1), -2);', "unsafe pointer address overflow"),
        "min_offset": ('unsafe_ptr_add(unsafe_ptr_from_handle(1), -9223372036854775808);', "unsafe pointer address overflow"),
        "range_load": ('unsafe_load<u64>(unsafe_ptr_from_handle(18446744073709551615), false);', "unsafe pointer address overflow"),
        "range_store": ('unsafe_store<u16>(unsafe_ptr_from_handle(18446744073709551615), 1, true);', "unsafe pointer address overflow"),
    }
    sources = [(fixture, "unsafe pointer ok", None)]
    for name, (statement, error) in errors.items():
        source = out / (name + ".goose")
        source.write_text("fn main() { " + statement + " }\n")
        sources.append((source, None, error))

    for level in (0, 2):
        for source, expected, error in sources:
            c = out / f"{source.stem}-O{level}.c"
            run([goose, f"-O{level}", "--standalone", "-o", c, source])
            generated = c.read_text()
            if source == fixture:
                assert "UINTPTR_MAX" in generated, "target width must be validated in generated C"
                assert "memcpy" in generated, "unaligned accesses must copy scalar bits"
                assert "gs_shared_read(" not in generated[generated.rfind("static void main_g"):], "raw access must not use shared-memory services"
            for name, compiler in compilers:
                for debug in (0, 1):
                    binary = out / f"{source.stem}-O{level}-{name}-debug{debug}"
                    run([compiler, f"-O{level}", f"-DGS_DEBUG={debug}", c, "-o", binary, "-lm", "-pthread", "-ldl"])
                    run([binary], error=error, output=expected)
            # Keep all UBSan checks enabled, including alignment.
            clang = compilers[1][1]
            binary = out / f"{source.stem}-O{level}-sanitize"
            run([clang, "-O1", "-g", "-DGS_DEBUG=1", "-fsanitize=address,undefined",
                 "-fno-sanitize-recover=all", "-fno-omit-frame-pointer", c,
                 "-o", binary, "-lm", "-pthread", "-ldl"])
            run([binary], error=error, output=expected)
    print(f"unsafe pointer: {checks} checks passed (GCC, Clang, debug/release, ASan/UBSan)")


if __name__ == "__main__":
    main()
