#!/usr/bin/env python3
"""Unknown raw writes must invalidate BCE without changing operand snapshots.

Every raw access targets a live writable i64 obtained from a test-only C
adapter. The only invalid operation is the subsequent safe array access,
which must abort before reading out of bounds.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=ROOT / "build/goose")
    args = parser.parse_args()
    goose = args.exe.resolve()
    fixtures = ROOT / "test/memory/unsafe_pointer_alias"
    out = ROOT / "build/gen/unsafe-pointer-alias"
    out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, GOOSE_HOME=str(ROOT / "build/unsafe-home"))
    checks = 0

    def run(argv, error=None, output=None):
        nonlocal checks
        result = subprocess.run([str(x) for x in argv], cwd=ROOT, env=env,
                                capture_output=True, text=True, timeout=120)
        text = result.stdout + result.stderr
        if error:
            assert result.returncode != 0 and error in text, (argv, result.returncode, text)
        else:
            assert result.returncode == 0, (argv, result.returncode, text)
        if output is not None:
            assert result.stdout.strip() == output, (argv, text)
        checks += 1
        return text

    compilers = [(name, shutil.which(name)) for name in ("gcc", "clang")]
    assert all(path for _, path in compilers), "GCC and Clang are required"
    sources = sorted(fixtures.glob("*.goose"))
    # Test BCE annotations first: a pre-fix compiler fails without executing
    # any unchecked safe index, making the regression safe to run when red.
    for source in sources:
        run([goose, "--roundtrip", "--check", "--bce-test", source])
    for level in (0, 1, 2):
        for source in sources:
            c = out / f"{source.stem}-O{level}.c"
            run([goose, f"-O{level}", "--bce-test", "--standalone", "--include",
                 fixtures / "adapter.h", "-o", c, source])
            error = None if source.stem == "values" else "index out of bounds"
            output = "unsafe alias values ok" if source.stem == "values" else ""
            for name, compiler in compilers:
                for native_level in (0, 2):
                    for debug in (0, 1):
                        binary = out / f"{source.stem}-g{level}-{name}-O{native_level}-d{debug}"
                        run([compiler, f"-O{native_level}", f"-DGS_DEBUG={debug}", c,
                             "-o", binary, "-lm", "-pthread", "-ldl"])
                        run([binary], error=error, output=output)
            binary = out / f"{source.stem}-g{level}-sanitize"
            run([compilers[1][1], "-O1", "-g", "-DGS_DEBUG=1", "-fsanitize=address,undefined",
                 "-fno-sanitize-recover=all", "-fno-omit-frame-pointer", c,
                 "-o", binary, "-lm", "-pthread", "-ldl"])
            run([binary], error=error, output=output)
    print(f"unsafe pointer alias effects: {checks} checks passed (BCE, values, GCC/Clang, ASan/UBSan)")


if __name__ == "__main__":
    main()
