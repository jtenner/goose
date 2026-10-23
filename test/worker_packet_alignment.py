"""Worker packets are byte packed, including their private image metadata."""
from pathlib import Path

import toolchain as tc


def check_worker_packet_alignment(exe, cc, base, *, runtime, extra=()):
    base = (Path(base) / "worker-packet-alignment").resolve()
    base.mkdir(parents=True, exist_ok=True)
    # Re-enable alignment after the ordinary sanitizer profile's flags.
    # Both the generated program and the separate runtime receive these flags.
    flags = [*extra, "-fsanitize=alignment", "-fno-sanitize-recover=all"]
    for kind in ("arguments", "globals", "alias", "fixed"):
        source = tc.REPO_ROOT / "test" / "threads" / f"worker_packet_{kind}.goose"
        for goose_level in (0, 2):
            cfile = base / f"{kind}-g{goose_level}.c"
            code, out, err = tc.run_capture([exe, f"-O{goose_level}", "-o", cfile, source])
            if code or tc.sanitizer_failure(err):
                raise RuntimeError(out + err)
            for c_level in (0, 2):
                for debug in (False, True):
                    label = f"{kind}-g{goose_level}-c{c_level}-d{int(debug)}"
                    binary = base / (label + tc.EXE_SUFFIX)
                    ok, log = cc.compile(cfile, binary, opt=c_level, extra=flags,
                                         defines=["GS_DEBUG=1"] if debug else [],
                                         strict_decls=True, runtime=runtime,
                                         log=base / (label + ".cc.log"))
                    if not ok:
                        raise RuntimeError(label + ":\n" + log)
                    code, out, err = tc.run_capture([binary])
                    tc.write_text(base / (label + ".stdout"), out)
                    tc.write_text(base / (label + ".stderr"), err)
                    if code or tc.sanitizer_failure(err):
                        raise RuntimeError(f"{label}: exit {code}\n{out}{err}")
                    if out.strip() != f"worker packet {kind} passed":
                        raise RuntimeError(label + ": unexpected output: " + out)
