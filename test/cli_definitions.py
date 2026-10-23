#!/usr/bin/env python3
"""Native --define acceptance tests. Run with the compiler path as argument."""
import pathlib
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
from lsp_protocol import Client

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
    source.write_text('fn defined() -> i64 { build::COUNT }\n'
                      'fn main() { let a: u8[3] = build::TEXT; '
                      'print(a, " ", build::TEXT[0], " ", build::TEXT[1..], " ", defined()); }\n')
    for level in ("-O0", "-O2"):
        invoke(["run", level, "--define", 'TEXT="abc"', "--define", "COUNT=8", source],
               contains="abc 97 bc 8")
    source.write_text('fn main() { build::TEXT[0] = 1; }\n')
    invoke(["check", "--define", 'TEXT="abc"', source], ok=False)
    source.write_text('let ALIAS = build::TEXT;\n'
                      'struct Buffer { bytes: u8[build::TEXT.len] }\n'
                      'fn main() { var a: u8[ALIAS.len] = [1; ALIAS.len]; '
                      'print(a.len, " ", match 3 { build::COUNT => "yes", _ => "no" }); }\n')
    for level in ("-O0", "-O2"):
        invoke(["run", level, "--roundtrip", "--define", 'TEXT="abc"', "--define", "COUNT=3", source],
               contains="3 yes")
    source.write_text('fn main() { print(build::COUNT); }\n')
    second = root / "second.goose"
    second.write_text(source.read_text())
    invoke(["--multi-test", "--check", "--define", "COUNT=3", source, second])
    invoke(["--define", "COUNT=3", "--define", "FLAG=true", source, "-o", generated])
    first_c = generated.read_text()
    invoke(["--define", "FLAG=true", "--define", "COUNT=3", source, "-o", generated])
    assert generated.read_text() == first_c
    # Imports and generic specializations use the same typed configuration.
    helper = root / "helper.goose"
    helper.write_text('fn configured<T>(value: T) -> i64 { build::COUNT }\n')
    source.write_text('import helper; fn main() { print(configured(1), " ", configured(true)); }\n')
    invoke(["run", "-O2", "--define", "COUNT=9", source], contains="9 9")
    # Native strings are constants for compile-time APIs too, directly and
    # through immutable global aliases. Relative paths belong to the source.
    payload = root / "native_definition_payload.bin"
    payload.write_bytes(b"embedded native definition")
    path_definition = ["--define", 'FILE="native_definition_payload.bin"']
    for level in ("-O0", "-O2"):
        source.write_text('fn main() { print(embed_file(build::FILE)); }\n')
        invoke(["run", level, *path_definition, source], contains="embedded native definition")
        invoke(["--roundtrip", "--check", level, *path_definition, source])
        invoke([level, *path_definition, source, "-o", generated])
        assert payload.name not in generated.read_text()
        source.write_text('let FILE = build::FILE; let ALIAS = FILE;\n'
                          'fn main() { print(embed_file(ALIAS)); }\n')
        invoke(["run", level, *path_definition, source], contains="embedded native definition")
        source.write_text('let FILE = build::FILE; let ALIAS = FILE;\n'
                          'fn main() { let FILE = "other.bin"; print(embed_file(ALIAS)); }\n')
        invoke(["run", level, *path_definition, source], contains="embedded native definition")
        # Local shadowing and mutable globals retain the existing restriction.
        source.write_text('let FILE = build::FILE;\n'
                          'fn main() { let FILE = "other.bin"; embed_file(FILE); }\n')
        invoke(["check", level, *path_definition, source], ok=False, contains="embed_file takes")
        source.write_text('var FILE = build::FILE;\nfn main() { embed_file(FILE); }\n')
        invoke(["check", level, *path_definition, source], ok=False, contains="embed_file takes")
        source.write_text('fn main() { embed_file(build::FILE); }\n')
        invoke(["check", level, "--define", "FILE=true", source], ok=False, contains="embed_file takes")
        source.write_text('fn main() { let shader = embed_shader(build::STAGE, build::GLSL); '
                          'print(shader.len > 0); }\n')
        invoke(["run", level, "--define", 'STAGE="frag"', "--define",
                'GLSL="layout(location = 0) out vec4 result; void main() { result = vec4(1.0); }"',
                source], contains="true")
    # The editor must report the same configuration and expose read-only symbols.
    text = 'fn main() { print(build::COUNT); }\n'
    source.write_text(text)
    uri = source.as_uri()
    client = Client(str(EXE), root, ["--define", "COUNT=3"])
    try:
        client.request("initialize", {"processId": None, "rootUri": root.as_uri(),
                                      "capabilities": {},
                                      "initializationOptions": {"entryFiles": [str(source)]}})
        client.send("initialized", {}, request=False)
        client.send("textDocument/didOpen", {"textDocument": {"uri": uri, "languageId": "goose",
                                                              "version": 1, "text": text}}, request=False)
        diagnostics = client.diagnostics_for(uri)
        assert diagnostics == [], diagnostics
        doc = {"textDocument": {"uri": uri}}
        position = {"line": 0, "character": text.index("COUNT") + 1}
        hover = client.request("textDocument/hover", {**doc, "position": position})
        assert "i64" in str(hover) and "--define" in str(hover), hover
        completion = client.request("textDocument/completion", {**doc, "position": position})
        assert any(item["label"] == "COUNT" and item["kind"] == 21 for item in completion["items"]), completion
        tokens = client.request("textDocument/semanticTokens/full", doc)["data"]
        assert any((tokens[i + 4] & 6) == 6 for i in range(0, len(tokens), 5)), tokens
        assert client.request("textDocument/definition", {**doc, "position": position}) is None
        client.request("shutdown", {})
        client.send("exit", {}, request=False)
        client.p.wait(timeout=10)
    finally:
        if client.p.poll() is None:
            client.p.kill()
            client.p.wait()
    # Native intermediates must be separated by configuration, independent of
    # option order. Concurrent builds may use the same source and different -o.
    def intermediate(definitions):
        result = invoke(["build", "--dry-run", *definitions, source, "-o", root / "dry-run"])
        return re.search(r"^wrote (.+) \(\d+ bytes\)$", result.stdout, re.MULTILINE).group(1)

    config_a = ["--define", "COUNT=11", "--define", "FLAG=true"]
    config_b = ["--define", "FLAG=true", "--define", "COUNT=11"]
    config_c = ["--define", "COUNT=22", "--define", "FLAG=true"]
    assert intermediate(config_a) == intermediate(config_b)
    assert intermediate(config_a) != intermediate(config_c)
    builds = []
    for index, count in enumerate((11, 22, 11, 22)):
        native = root / f"concurrent-{index}"
        proc = subprocess.Popen([str(EXE), "build", "--define", f"COUNT={count}", str(source),
                                 "-o", str(native)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        builds.append((proc, native, count))
    for proc, native, count in builds:
        out, err = proc.communicate(timeout=60)
        assert proc.returncode == 0, (out, err)
        result = subprocess.run([str(native)], capture_output=True, text=True, check=True)
        assert result.stdout == f"{count}\n", (count, result.stdout)

print(f"CLI definitions: {CHECKS} checks passed")
