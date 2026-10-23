"""Builder result channels must obey C scalar alignment even with packed headers."""
from pathlib import Path

import toolchain as tc


def check_builder_return_alignment(exe, cc, base, *, runtime, extra=()):
    base = (Path(base) / "builder-return-alignment").resolve()
    base.mkdir(parents=True, exist_ok=True)
    source = tc.REPO_ROOT / "test" / "codegen" / "builder_return_alignment.goose"
    # The ordinary sanitizer profile disables alignment for raw packed scalar
    # accesses. This focused regression must retain it, in either profile.
    flags = [*extra, "-fsanitize=alignment", "-fno-sanitize-recover=all"]
    for goose_level in (0, 2):
        cfile = base / f"return-{goose_level}.c"
        code, out, err = tc.run_capture([exe, f"-O{goose_level}", "-o", cfile, source])
        if code or tc.sanitizer_failure(err):
            raise RuntimeError(out + err)
        for c_level in (0, 2):
            binary = base / f"return-{goose_level}-{c_level}{tc.EXE_SUFFIX}"
            ok, log = cc.compile(cfile, binary, opt=c_level, extra=flags,
                                 strict_decls=True, runtime=runtime)
            if not ok:
                raise RuntimeError(log)
            code, out, err = tc.run_capture([binary])
            if code or tc.sanitizer_failure(err):
                raise RuntimeError(f"Goose O{goose_level}, C O{c_level}:\n" + out + err)
            if out.strip() != "builder return alignment passed":
                raise RuntimeError("unexpected builder-return-alignment output: " + out)
