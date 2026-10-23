#!/usr/bin/env python3
"""Native --define acceptance tests. Run with the compiler path as argument."""
import pathlib
import subprocess
import sys
import tempfile

EXE = pathlib.Path(sys.argv[1]).resolve()
CHECKS = 0


def invoke(args, *, ok=True, contains=None):
    global CHECKS
    result = subprocess.run([str(EXE), *map(str, args)], capture_output=True, text=True)
    output = result.stdout + result.stderr
    assert (result.returncode == 0) == ok, (args, result.returncode, output)
    if contains is not None:
        assert contains in output, (args, contains, output)
    CHECKS += 1
    return result


with tempfile.TemporaryDirectory(prefix="goose-definitions-") as directory:
    root = pathlib.Path(directory)
    source = root / "main.goose"
    source.write_text('fn main() { print(build::FLAG, " ", build::COUNT, " ", build::TEXT); }\n')
    for level in ("-O0", "-O2"):
        for flag in ("true", "false"):
            for count in ("0", "8", "-8", "9223372036854775807", "-9223372036854775808", "18446744073709551615"):
                definitions = ["--define", "FLAG=" + flag, "--define", "COUNT=" + count,
                               "--define", 'TEXT="hello\\nworld"']
                invoke(["check", level, *definitions, source])
                result = invoke(["run", level, *definitions, source])
                assert result.stdout == f"{flag} {count} hello\nworld\n", result.stdout
    definitions = ["--define", "FLAG=true", "--define", "COUNT=8", "--define", 'TEXT="native"']
    native = root / "native"
    invoke(["build", *definitions, source, "-o", native])
    result = subprocess.run([str(native)], capture_output=True, text=True, check=True)
    assert result.stdout == "true 8 native\n"
    generated = root / "main.c"
    invoke([*definitions, source, "-o", generated])
    c = generated.read_text()
    assert "#define FLAG" not in c and "#define COUNT" not in c and "#define TEXT" not in c
    # Unused definitions must introduce no runtime data, including strings.
    source.write_text('fn main() { print("ok"); }\n')
    invoke(["--define", 'UNUSED="unused_cli_definition_sentinel"', "-DLEGACY=17", source, "-o", generated])
    c = generated.read_text()
    assert "unused_cli_definition_sentinel" not in c
    assert "#define LEGACY 17" in c
    for value in ("X", "X=", "=true", "0X=true", "a::b=true", "X=1+2", "X=1.5",
                  "X=18446744073709551616", "X=-9223372036854775809", 'X="bad', "if=true"):
        invoke(["check", "--define", value, source], ok=False, contains="--define")
    invoke(["check", source, "--define"], ok=False, contains="--define")
    invoke(["check", "--define", "X=true", "--define", "X=true", source], ok=False, contains="duplicate")
    source.write_text('fn main() { print(build::MISSING); }\n')
    invoke(["check", source], ok=False, contains="MISSING")
    for declaration in ('let build::FLAG = false;', 'struct build::Thing {}', 'fn build::f() {}'):
        source.write_text(declaration + '\nfn main() {}\n')
        invoke(["check", "--define", "FLAG=true", source], ok=False, contains="reserved")
    source.write_text('fn main() { build::FLAG = false; }\n')
    invoke(["check", "--define", "FLAG=true", source], ok=False)
    source.write_text('fn main() { var a: u8[build::COUNT] = [0; build::COUNT]; print(a.len); }\n')
    invoke(["run", "--define", "COUNT=8", source], contains="8")

print(f"CLI definitions: {CHECKS} checks passed")
