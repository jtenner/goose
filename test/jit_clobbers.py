#!/usr/bin/env python3
"""Phase10: checks track actual ownership; false config is absent even at O0."""
from pathlib import Path
import shutil
import sys
import tempfile
from native_examples_support import ROOT, build, run

EXE = Path(sys.argv[1]).resolve()
SOURCE = ROOT / "samples/jit_clobbers/main.goose"
with tempfile.TemporaryDirectory(prefix="goose-clobber-") as directory:
    root = Path(directory)
    for level in ("-O0", "-O2"):
        for checks in (False, True):
            for assertions in (False, True):
                flags = [level, "--define", "CHECK_REGISTER_CLOBBERS=" + str(checks).lower(),
                         "--define", "ENABLE_JIT_ASSERTIONS=" + str(assertions).lower()]
                generated = root / "clobber.c"
                run([EXE, *flags, SOURCE, "-o", generated])
                c = generated.read_text()
                for marker in ("register_owners", "validate_register_ownership", "REGISTER_CLOBBER_SENTINEL"):
                    assert (marker in c) == checks, (level, checks, marker)
                assert ("JIT_ASSERTION_SENTINEL" in c) == assertions
                app = build(EXE, SOURCE, root / "clobber", *flags)
                assert run([app]).stdout.strip() == "b80700000050b80b00000050595801c85058c3"
                run([app, "clobber"], ok=not checks)
                run([app, "assertion"], ok=not assertions)
                if shutil.which("objdump"):
                    disassembly = run(["objdump", "-d", app]).stdout
                    if not checks:
                        assert "validate_register_ownership" not in disassembly
                    symbols = run(["objdump", "-t", app]).stdout
                    if not checks:
                        assert "validate_register_ownership" not in symbols
print("conditional clobber acceptance passed")
