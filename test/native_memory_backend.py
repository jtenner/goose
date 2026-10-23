"""The complete inline atomic path needs lock-free descriptor generations.
Cross-compiles a U32-only gate without system headers, so a host lacking a
32-bit sysroot can still reject i486's non-lock-free 64-bit validator."""
import re
import subprocess
import tempfile
from pathlib import Path


def check_native_memory_backend(exe, clang, base):
    base = Path(base).resolve()
    base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="native-memory-", dir=base) as tmp:
        root = Path(tmp)
        source = root / "only32.goose"
        source.write_text('fn main() { let o, ok = shared_alloc(8); assert(ok); '
                          'let a = shared_atomic_u32(o, 0, 0); '
                          'atomic_fetch_add(a, 1, "Relaxed"); assert(shared_close(o)); }\n')
        generated = root / "only32.c"
        built = subprocess.run([str(exe), "-O2", "-o", str(generated), str(source)],
                               capture_output=True, text=True, timeout=60)
        if built.returncode:
            raise RuntimeError(built.stdout + built.stderr)
        text = generated.read_text()
        gates = "\n".join(re.findall(r"^#if __GCC_ATOMIC_.*?^#endif$", text, re.M | re.S))
        if not gates:
            raise RuntimeError("native atomic backend emitted no lock-free capability gate")

        def compile_c(code, target, march=None):
            cmd = [str(clang.cc), "-target", target, "-ffreestanding", "-std=c11",
                   "-fsyntax-only", "-x", "c", "-"]
            if march:
                cmd += ["-march=" + march]
            return subprocess.run(cmd, input=code, capture_output=True, text=True, timeout=60)

        unsupported = compile_c(gates + "\nint probe;\n", "i386-unknown-linux-gnu", "i486")
        if "No available targets" in unsupported.stderr or "unknown target" in unsupported.stderr:
            return "clang has no i386 cross-compilation target"
        if unsupported.returncode == 0 or "generation" not in unsupported.stderr:
            raise RuntimeError("U32 capability gate failed to reject a non-lock-free 64-bit "
                               "generation validator:\n" + unsupported.stdout + unsupported.stderr)
        supported = compile_c(gates + "\nint probe;\n", "x86_64-unknown-linux-gnu")
        if supported.returncode:
            raise RuntimeError("always-lock-free x86-64 backend rejected:\n" + supported.stderr)
        record = re.search(r"typedef struct(?: GS_SHARED_ALIGN8)? gs_shared_record \{.*?"
                           r"\} gs_shared_record;", text, re.S)
        if not record:
            raise RuntimeError("cannot find actual descriptor declaration")
        layout = ("typedef __UINT64_TYPE__ uint64_t; typedef __INT64_TYPE__ int64_t; "
                  "typedef unsigned char uint8_t;\n"
                  "#define GS_SHARED_ALIGN8 __attribute__((aligned(8)))\n" + record[0] +
                  '\n_Static_assert(_Alignof(gs_shared_record) >= 8, "generation alignment");\n'
                  '_Static_assert(sizeof(gs_shared_record) % 8 == 0, "slab stride alignment");\n')
        aligned = compile_c(layout, "i386-unknown-linux-gnu", "i486")
        if aligned.returncode:
            raise RuntimeError("descriptor generations lack 8-byte slab alignment:\n" + aligned.stderr)
    return None
