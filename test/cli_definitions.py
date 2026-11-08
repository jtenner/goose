#!/usr/bin/env python3
"""Native -D acceptance tests. Run with the compiler path as argument."""
import pathlib
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
from lsp_protocol import Client

EXE = pathlib.Path(sys.argv[1]).resolve()
CHECKS = 0


def without_macros(text, *names):
    prefixes = tuple("#define " + name + " " for name in names)
    return "\n".join(line for line in text.splitlines() if not line.startswith(prefixes))


def invoke(args, *, ok=True, contains=None, env=None):
    global CHECKS
    result = subprocess.run([str(EXE), *map(str, args)], capture_output=True, text=True, env=env)
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
                definitions = ["-D", "FLAG=" + flag, "-D", "COUNT=" + count,
                               "-D", 'TEXT="hello\\nworld"']
                invoke(["check", level, *definitions, source])
                result = invoke(["run", level, *definitions, source])
                assert result.stdout == f"{flag} {count} hello\nworld\n", result.stdout
    definitions = ["-D", "FLAG=true", "-D", "COUNT=8", "-D", 'TEXT="native"']
    native = root / "native"
    invoke(["build", *definitions, source, "-o", native])
    result = subprocess.run([str(native)], capture_output=True, text=True, check=True)
    assert result.stdout == "true 8 native\n"
    generated = root / "main.c"
    invoke([*definitions, source, "-o", generated])
    c = generated.read_text()
    assert "#define FLAG true" in c and "#define COUNT 8" in c and '#define TEXT "native"' in c
    # Unused definitions must introduce no runtime data, including strings.
    source.write_text('fn main() { print("ok"); }\n')
    invoke(["-D", 'UNUSED="unused_cli_definition_sentinel"', "-DLEGACY=17", source, "-o", generated])
    c = generated.read_text()
    assert '#define UNUSED "unused_cli_definition_sentinel"' in c
    assert "unused_cli_definition_sentinel" not in without_macros(c, "UNUSED")
    assert "#define LEGACY 17" in c
    for value in ("X", "X=", "=true", "0X=true", "a::b=true", "X=1+2", "X=1.5",
                  "X=18446744073709551616", "X=-9223372036854775809", 'X="bad', "if=true"):
        invoke(["check", "-D", value, source])
    invoke(["check", source, "-D"], ok=False, contains="unknown option")
    invoke(["check", source, "-d"], ok=False, contains="requires an attached define")
    invoke(["check", "--define", "FLAG=true", source], ok=False, contains="unknown option")
    invoke(["lsp", "--define", "FLAG=true"], ok=False, contains="unknown option")
    invoke(["lsp", "-d"], ok=False, contains="requires an attached define")
    invoke(["check", "-D", "X=true", "-D", "X=true", source], ok=False, contains="duplicate")
    source.write_text('fn main() { print(build::MISSING); }\n')
    invoke(["check", source], ok=False, contains="MISSING")
    for declaration in ('let build::FLAG = false;', 'struct build::Thing {}', 'fn build::f() {}'):
        source.write_text(declaration + '\nfn main() {}\n')
        invoke(["check", "-D", "FLAG=true", source], ok=False, contains="reserved")
    source.write_text('fn main() { build::FLAG = false; }\n')
    invoke(["check", "-D", "FLAG=true", source], ok=False)
    source.write_text('fn main() { var a: u8[build::COUNT] = [0; build::COUNT]; print(a.len); }\n')
    invoke(["run", "-D", "COUNT=8", source], contains="8")
    source.write_text('fn defined() -> i64 { build::COUNT }\n'
                      'fn main() { let a: u8[3] = build::TEXT; '
                      'print(a, " ", build::TEXT[0], " ", build::TEXT[1..], " ", defined()); }\n')
    for level in ("-O0", "-O2"):
        invoke(["run", level, "-D", 'TEXT="abc"', "-D", "COUNT=8", source],
               contains="abc 97 bc 8")
    source.write_text('fn main() { build::TEXT[0] = 1; }\n')
    invoke(["check", "-D", 'TEXT="abc"', source], ok=False)
    source.write_text('let ALIAS = build::TEXT;\n'
                      'struct Buffer { bytes: u8[build::TEXT.len] }\n'
                      'fn main() { var a: u8[ALIAS.len] = [1; ALIAS.len]; '
                      'print(a.len, " ", match 3 { build::COUNT => "yes", _ => "no" }); }\n')
    for level in ("-O0", "-O2"):
        invoke(["run", level, "--roundtrip", "-D", 'TEXT="abc"', "-D", "COUNT=3", source],
               contains="3 yes")
    source.write_text('fn main() { print(build::COUNT); }\n')
    second = root / "second.goose"
    second.write_text(source.read_text())
    invoke(["--multi-test", "--check", "-D", "COUNT=3", source, second])
    invoke(["-D", "COUNT=3", "-D", "FLAG=true", source, "-o", generated])
    first_c = generated.read_text()
    invoke(["-D", "FLAG=true", "-D", "COUNT=3", source, "-o", generated])
    assert without_macros(generated.read_text(), "COUNT", "FLAG") == without_macros(first_c, "COUNT", "FLAG")
    # All public spellings produce the same constants and the same C text.
    source.write_text('fn main() { print(build::FLAG, " ", build::COUNT, " ", build::TEXT); }\n')
    reference = None
    for definitions in (["-D", "FLAG=true", "-D", "COUNT=17uLL", "-D", 'TEXT="typed"'],
                        ["-DFLAG=true", "-DCOUNT=17uLL", '-DTEXT="typed"'],
                        ["-dFLAG=true", "-dCOUNT=17uLL", '-dTEXT="typed"']):
        invoke(["run", *definitions, source], contains="true 17 typed")
        invoke([*definitions, source, "-o", generated])
        if reference is None:
            reference = generated.read_bytes()
        assert generated.read_bytes() == reference
    source.write_text('fn main() { print(build::NUMBER); }\n')
    for value, expected in (("+17", "17"), ("-0", "0"), ("17u", "17"), ("17L", "17"),
                            ("17Ul", "17"), ("17lU", "17"), ("17ULL", "17"), ("17llU", "17"),
                            ("2K", "2048"), ("2m", "2097152"), ("1G", "1073741824"),
                            ("1t", "1099511627776"), ("-2K", "-2048"),
                            ("-9223372036854775808LL", "-9223372036854775808"),
                            ("18446744073709551615ULL", "18446744073709551615")):
        invoke(["run", "-dNUMBER=" + value, source], contains=expected)
    for value in ("0x10", "(1 << 10)", "1+2", "1.5", "1uuu", "1KB", "18446744073709551616",
                  "18014398509481984K", "-9223372036854775809", '"bad', '"ok" ', '"ok"+"more"'):
        invoke(["check", "-DNUMBER=" + value, source], ok=False, contains="unknown identifier")
        unused = root / "unused.goose"
        unused.write_text('fn main() {}\n')
        invoke(["-DNUMBER=" + value, unused, "-o", generated])
        assert "#define NUMBER " + value + "\n" in generated.read_text()
    invoke(["run", "-DNUMBER", source], contains="1")
    invoke(["run", "-dNUMBER", source], contains="1")
    invoke(["check", "-D", "NUMBER=1", "-dNUMBER=1", source], ok=False, contains="duplicate")
    invoke(["check", "-DNUMBER", "-dNUMBER=1", source], ok=False, contains="duplicate")
    # Compiler-internal macros do not create Goose constants. Explicit input wins there.
    for internal in ("GS_DEBUG", "GS_STACK_RESERVE", "GS_SEPARATE_RUNTIME", "GS_NEED_THREADS"):
        source.write_text('fn main() { print(build::' + internal + '); }\n')
        invoke(["check", "--debug", "--stack-reserve", "64K", source], ok=False, contains=internal)
        source.write_text('fn main() { const if build::' + internal +
                          ' == 7 {} else { wrong_definition(); } }\n')
        definition = "-d" + internal + "=7"
        invoke(["check", "--debug", "--stack-reserve", "64K", definition, source])
        invoke(["check", definition, "--debug", "--stack-reserve", "64K", source])
    # Goose keywords and function-like macros remain C-only inputs.
    source.write_text('fn main() {}\n')
    for definition in ("if=true", "F(x)=((x)+1)", "X=1+2", "EMPTY="):
        invoke(["-D" + definition, source, "-o", generated])
        name, value = definition.split("=", 1)
        assert f"#define {name} {value}\n" in generated.read_text()
    # Sidecars use the same grammar, including platform lists and imported packages.
    source.write_text('fn main() { print(build::SIDE_BOOL, " ", build::SIDE_N, " ", build::SIDE_TEXT); }\n')
    sidecar = source.with_suffix(".build")
    sidecar.write_text('c_defines = ["SIDE_BOOL=true", "SIDE_N=2K", "SIDE_TEXT=\\\"side\\\""];\n')
    invoke(["run", "--roundtrip", source], contains="true 2048 side")
    invoke(["check", "-dSIDE_N=2K", source], ok=False, contains="duplicate")
    platform = "windows" if sys.platform == "win32" else "macos" if sys.platform == "darwin" else "linux"
    sidecar.write_text(sidecar.read_text() + f'c_defines_{platform} = ["PLATFORM_N=9UL"];\n')
    saved = source.read_text()
    source.write_text('fn main() { print(build::PLATFORM_N); }\n')
    invoke(["run", "--roundtrip", source], contains="9")
    invoke(["check", "-DPLATFORM_N=9", source], ok=False, contains="duplicate")
    source.write_text(saved)
    package = root / "package"
    package.mkdir()
    (package / "pkg.goose").write_text('fn package_value() -> i64 { build::FROM_PKG }\n')
    (package / "pkg.build").write_text('c_defines = ["FROM_PKG=5UL"];\n')
    source.write_text('import pkg from "./package"; fn main() { print(package_value(), " ", build::SIDE_N); }\n')
    invoke(["run", "--roundtrip", source], contains="5 2048")
    invoke(["check", "-DFROM_PKG=5", source], ok=False, contains="duplicate")
    (package / "pkg.build").write_text('c_defines = ["SIDE_N=3"];\n')
    invoke(["check", source], ok=False, contains="duplicate")
    sidecar.unlink()
    source.write_text('fn main() { print(build::COUNT); }\n')
    # Imports and generic specializations use the same typed configuration.
    helper = root / "helper.goose"
    helper.write_text('fn configured<T>(value: T) -> i64 { build::COUNT }\n')
    source.write_text('import helper; fn main() { print(configured(1), " ", configured(true)); }\n')
    invoke(["run", "-O2", "-D", "COUNT=9", source], contains="9 9")
    # Native strings are constants for compile-time APIs too, directly and
    # through immutable global aliases. Relative paths belong to the source.
    payload = root / "native_definition_payload.bin"
    payload.write_bytes(b"embedded native definition")
    path_definition = ["-D", 'FILE="native_definition_payload.bin"']
    for level in ("-O0", "-O2"):
        source.write_text('fn main() { print(embed_file(build::FILE)); }\n')
        invoke(["run", level, *path_definition, source], contains="embedded native definition")
        invoke(["--roundtrip", "--check", level, *path_definition, source])
        invoke([level, *path_definition, source, "-o", generated])
        assert payload.name not in without_macros(generated.read_text(), "FILE")
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
        invoke(["check", level, "-D", "FILE=true", source], ok=False, contains="embed_file takes")
        source.write_text('fn main() { let shader = embed_shader(build::STAGE, build::GLSL); '
                          'print(shader.len > 0); }\n')
        invoke(["run", level, "-D", 'STAGE="frag"', "-D",
                'GLSL="layout(location = 0) out vec4 result; void main() { result = vec4(1.0); }"',
                source], contains="true")
    # Definition literals have synthetic declaration positions. Shader errors
    # must use each argument's actual file/line, including imported aliases.
    valid_glsl = "layout(location = 0) out vec4 result; void main() { result = vec4(1.0); }"
    editor_cases = []
    for imported in (False, True):
        for aliased in (False, True):
            target = root / "shader_helper.goose" if imported else source
            prefix = ('let STAGE = build::STAGE; let GLSL = build::GLSL;\n' if aliased
                      else '// an unrelated first line\n')
            names = ("STAGE", "GLSL") if aliased else ("build::STAGE", "build::GLSL")
            text = prefix + '\nfn shader() {\n    let blob = embed_shader(' + names[0] + ', ' + names[1] + ');\n}\n'
            target.write_text(text + ('\nfn main() { shader(); }\n' if not imported else ''))
            if imported:
                source.write_text('import shader_helper;\nfn main() { shader(); }\n')
            for stage, glsl in (("fragment", valid_glsl), ("frag", valid_glsl.replace("1.0", "oops"))):
                flags = ["-D", "STAGE=" + json.dumps(stage), "-D", "GLSL=" + json.dumps(glsl)]
                for level in ("-O0", "-O2"):
                    result = invoke(["check", "--diagnostics", "json", level, *flags, source], ok=False)
                    diagnostics = json.loads(result.stdout)
                    errors = [d for d in diagnostics if d["severity"] == "error"]
                    assert errors and all(pathlib.Path(d["file"]).resolve() == target.resolve()
                                          and d["line"] == 4 for d in errors), diagnostics
                editor_cases.append((target, target.read_text(), flags, source.read_text()))
    for target, text, flags, main_text in editor_cases:
        target.write_text(text)
        if target != source:
            source.write_text(main_text)
        client = Client(str(EXE), root, flags)
        try:
            client.request("initialize", {"processId": None, "rootUri": root.as_uri(), "capabilities": {},
                                          "initializationOptions": {"entryFiles": [str(source)]}})
            client.send("initialized", {}, request=False)
            client.send("textDocument/didOpen", {"textDocument": {"uri": target.as_uri(), "languageId": "goose",
                                                                  "version": 1, "text": text}}, request=False)
            diagnostics = client.diagnostics_for(target.as_uri())
            assert diagnostics and all(d["range"]["start"]["line"] == 3 for d in diagnostics), diagnostics
            client.request("shutdown", {})
            client.send("exit", {}, request=False)
            client.p.wait(timeout=10)
        finally:
            if client.p.poll() is None:
                client.p.kill()
                client.p.wait()
    # The editor must report the same configuration and expose read-only symbols.
    text = 'fn main() { print(build::COUNT); }\n'
    source.write_text(text)
    uri = source.as_uri()
    client = Client(str(EXE), root, ["-D", "COUNT=3"])
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
        assert "i64" in str(hover) and "-D" in str(hover), hover
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
    for flags in (["-DCOUNT=3"], ["-dCOUNT=3"], []):
        sidecar = source.with_suffix(".build")
        if not flags:
            sidecar.write_text('c_defines = ["COUNT=3"];\n')
        client = Client(str(EXE), root, flags)
        try:
            client.request("initialize", {"processId": None, "rootUri": root.as_uri(), "capabilities": {},
                                          "initializationOptions": {"entryFiles": [str(source)]}})
            client.send("initialized", {}, request=False)
            client.send("textDocument/didOpen", {"textDocument": {"uri": uri, "languageId": "goose",
                                                                  "version": 1, "text": text}}, request=False)
            assert client.diagnostics_for(uri) == []
            hover = client.request("textDocument/hover", {"textDocument": {"uri": uri}, "position": position})
            assert "i64" in str(hover) and "-D/-d" in str(hover), hover
            CHECKS += 1
            client.request("shutdown", {})
            client.send("exit", {}, request=False)
            client.p.wait(timeout=10)
        finally:
            if client.p.poll() is None:
                client.p.kill()
                client.p.wait()
            sidecar.unlink(missing_ok=True)
    # Native intermediates must be separated by configuration, independent of
    # option order. Concurrent builds may use the same source and different -o.
    home = root / "intermediate-home"
    env = dict(os.environ, GOOSE_HOME=str(home))
    expected = root / "expected.c"

    def intermediate(definitions):
        pattern = f"build/prog/*/defines-*/{source.stem}.c"
        for path in home.glob(pattern):
            path.unlink()
        expected.unlink(missing_ok=True)
        invoke([*definitions, source, "-o", expected], env=env)
        assert expected.is_file(), expected
        expected_bytes = expected.read_bytes()
        assert expected_bytes, expected
        result = invoke(["build", "--dry-run", *definitions, source,
                         "-o", root / "dry-run"], env=env)
        paths = list(home.glob(pattern))
        assert len(paths) == 1, (paths, result.stdout, result.stderr)
        path = paths[0]
        assert path.is_file(), path
        assert path.stat().st_size == len(expected_bytes), path
        assert path.read_bytes() == expected_bytes, path
        return path

    config_a = ["-D", "COUNT=11", "-D", "FLAG=true"]
    config_b = ["-D", "FLAG=true", "-D", "COUNT=11"]
    config_c = ["-D", "COUNT=22", "-D", "FLAG=true"]
    assert intermediate(config_a) == intermediate(config_b)
    assert intermediate(config_a) != intermediate(config_c)
    sidecar = source.with_suffix(".build")
    sidecar.write_text('c_defines = ["CACHE_SIDE=1"];\n')
    side_a = intermediate(config_a)
    sidecar.write_text('c_defines = ["CACHE_SIDE=2"];\n')
    assert intermediate(config_a) != side_a
    sidecar.unlink()
    # C-only redefinitions keep input order in the cache key.
    assert intermediate([*config_a, "-DC_ONLY=1+2", "-DC_ONLY=3+4"]) != intermediate(
        [*config_a, "-DC_ONLY=3+4", "-DC_ONLY=1+2"])
    for a, b in (("F(x)=((x)+1)", "F(y)=((y)+2)"), ("F=1+2", "F(x)=((x)+1)"),
                 ("F =1+2", "F=3+4")):
        assert intermediate([*config_a, "-D" + a, "-D" + b]) != intermediate(
            [*config_a, "-D" + b, "-D" + a])
    builds = []
    for index, count in enumerate((11, 22, 11, 22)):
        native = root / f"concurrent-{index}"
        proc = subprocess.Popen([str(EXE), "build", "-D", f"COUNT={count}", str(source),
                                 "-o", str(native)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        builds.append((proc, native, count))
    for proc, native, count in builds:
        out, err = proc.communicate(timeout=60)
        assert proc.returncode == 0, (out, err)
        result = subprocess.run([str(native)], capture_output=True, text=True, check=True)
        assert result.stdout == f"{count}\n", (count, result.stdout)

print(f"CLI definitions: {CHECKS} checks passed")
