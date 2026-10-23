#!/usr/bin/env python3
"""Mandatory conditional-layout/shared-memory integration (native GCC/Clang).
Default executes every matrix entry with alignment sanitizer ENABLED.
--compile-only prepares/inspects without running programs while fixes land.
"""
import argparse
import json
from pathlib import Path
import shutil
import struct
import tempfile
from native_examples_support import ROOT, run

SOURCE = ROOT / "test/memory/conditional_shared_layout.goose"


def definitions(debug):
    return ["--define", "DEBUG=" + str(debug).lower()]


def negative_checks(goose, root):
    count = 0
    for level in ("-O0", "-O2"):
        for width in (32, 64):
            declaration = ("struct Packed { prefix: u8, const if build::DEBUG { "
                           f"conditional_token{width}: SharedAtomicU{width}, "
                           "} else {}, tail: u8 }\n")
            source = root / "negative.goose"
            source.write_text(declaration + "fn main() { let x = Packed { prefix: 1, tail: 2 }; "
                              f"let token = x.conditional_token{width}; }}\n")
            p = run([goose, "check", level, *definitions(False), source], ok=False)
            assert f"conditional_token{width}" in p.stderr, p.stderr
            count += 1
            for operation in ("bytes_of", "to_bytes", "from_bytes"):
                if operation == "from_bytes":
                    body = 'let forged, ok = from_bytes<Packed[>..]>(""); print(ok);'
                else:
                    body = (f"let o, ok = shared_alloc(64); assert(ok); let t = shared_atomic_u{width}(o, 0, 0); "
                            f"let x = Packed {{ prefix: 1, const if build::DEBUG {{ conditional_token{width}: t, }} else {{}}, tail: 2 }}; "
                            "var live: Packed[1] = [x]; " +
                            ("print(bytes_of(live).len);" if operation == "bytes_of" else "let image = to_bytes(live);"))
                source.write_text(declaration + "fn main() { " + body + " }\n")
                p = run([goose, "check", level, *definitions(True), source], ok=False)
                assert "native capabilities cannot be serialized" in p.stderr, (operation, p.stderr)
                count += 1
    return count


def exercise(app, root, enabled):
    expected_size, expected_offset = (16, 12) if enabled else (8, 4)
    accepted = f"accepted {expected_size} {expected_offset} 287454021\n"
    assert run([app]).stdout == accepted
    own = root / "own.wire"
    other = root / "other.wire"
    run([app, "emit", own])
    wire = own.read_bytes()
    assert len(wire) == 24 + expected_size
    assert struct.unpack_from("<6I", wire) == (0x47434853, 1, 0x48440000 + expected_size,
                                                  expected_size, expected_offset, 0)
    assert run([app, "consume", own, len(wire)]).stdout == accepted
    # A real producer of the other configuration supplies this file below.
    if other.exists():
        p = run([app, "consume", other, other.stat().st_size], ok=False)
        assert p.returncode == 2 and p.stdout == "rejected layout\n", (p.stdout, p.stderr)
    # Independent size/signature/offset/magic/version tampering must reject
    # BEFORE interpreting the application payload or publishing a result.
    for offset in (0, 4, 8, 12, 16, 20):
        changed = bytearray(wire)
        struct.pack_into("<I", changed, offset, struct.unpack_from("<I", wire, offset)[0] ^ 1)
        broken = root / "broken.wire"
        broken.write_bytes(changed)
        p = run([app, "consume", broken, len(changed)], ok=False)
        assert p.returncode == 2 and p.stdout == "rejected layout\n", (offset, p.stdout, p.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("goose", type=Path)
    ap.add_argument("--cc", action="append", help="GCC or Clang path; default both when available")
    ap.add_argument("--compile-only", action="store_true")
    ap.add_argument("--report", type=Path)
    ns = ap.parse_args()
    compilers = ns.cc or [shutil.which(x) for x in ("gcc", "clang") if shutil.which(x)]
    if not compilers:
        ap.error("GCC or Clang is required")
    goose = ns.goose.resolve()
    report = {"alignment_sanitizer": True, "executed": not ns.compile_only, "matrix": []}
    with tempfile.TemporaryDirectory(prefix="goose-conditional-shared-") as directory:
        root = Path(directory)
        # Missing source is a red regression before the standalone fixture lands.
        assert SOURCE.exists(), SOURCE
        report["negative_checks"] = negative_checks(goose, root)
        for goose_level in ("-O0", "-O2"):
            for runtime_debug in (False, True):
                artifacts = {}
                for enabled in (False, True):
                    cfile = root / f"layout-{enabled}.c"
                    flags = [goose_level, *definitions(enabled)] + (["--debug"] if runtime_debug else [])
                    run([goose, "--standalone", *flags, SOURCE, "-o", cfile])
                    c = cfile.read_text()
                    for marker in ("conditional_token32", "conditional_token64"):
                        assert (marker in c) == enabled, (enabled, marker)
                    artifacts[enabled] = c
                for compiler in compilers:
                    identity = run([compiler, "--version"]).stdout.splitlines()[0]
                    for native_level in ("-O0", "-O2"):
                        programs = {}
                        for enabled in (False, True):
                            cfile = root / f"native-{enabled}.c"
                            cfile.write_text(artifacts[enabled])
                            app = root / f"layout-{enabled}"
                            native_flags = [native_level, "-std=c11", "-pthread", "-g",
                                            "-fsanitize=alignment", "-fno-sanitize-recover=all"]
                            run([compiler, *native_flags, cfile, "-lm", "-o", app], timeout=600)
                            programs[enabled] = app
                            report["matrix"].append({"compiler": identity, "compiler_path": compiler,
                                "goose_optimization": goose_level, "runtime_debug": runtime_debug,
                                "DEBUG": enabled, "native_flags": native_flags})
                        if ns.compile_only:
                            continue
                        # Generate both actual producer formats, then cross-read.
                        for enabled, app in programs.items():
                            run([app, "emit", root / f"producer-{enabled}.wire"])
                        for enabled, app in programs.items():
                            shutil.copyfile(root / f"producer-{not enabled}.wire", root / "other.wire")
                            exercise(app, root, enabled)
    if ns.report:
        ns.report.write_text(json.dumps(report, indent=2) + "\n")
    verb = "compiled (not executed)" if ns.compile_only else "passed"
    print(f"conditional shared integration: {len(report['matrix'])} native configurations {verb}; "
          f"{report['negative_checks']} rejection checks; alignment sanitizer ENABLED")


if __name__ == "__main__":
    main()
