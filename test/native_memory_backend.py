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

        pointer_source = root / "pointer_only.goose"
        pointer_source.write_text('fn main() { let p, o, ok = shared_pointer_alloc<i64>(7); '
                                  'assert(ok); shared_pointer_release(p); assert(shared_close(o)); }\n')
        pointer_c = root / "pointer_only.c"
        built = subprocess.run([str(exe), "-O2", "-o", str(pointer_c), str(pointer_source)],
                               capture_output=True, text=True, timeout=60)
        if built.returncode:
            raise RuntimeError(built.stdout + built.stderr)
        pointer_text = pointer_c.read_text()
        backend_gate = re.search(r"^#if defined\(__TINYC__\) \|\| \(!defined\(__GNUC__\) && !defined\(__clang__\)\)\n"
                                 r"#error Native shared pointers require GCC or Clang; this backend is unsupported\n"
                                 r"#endif$",
                                 pointer_text, re.M | re.S)
        lock_gate = re.search(r"^#if __GCC_ATOMIC_LLONG_LOCK_FREE != 2\n"
                              r"#error Native shared pointer.*?^#endif$",
                              pointer_text, re.M | re.S)
        if not backend_gate or not lock_gate:
            raise RuntimeError("pointer-only program emitted no complete backend/lock-free gate")
        pointer_gates = backend_gate[0] + "\n" + lock_gate[0]
        unsupported_pointer = compile_c(pointer_gates + "\nint probe;\n",
                                        "i386-unknown-linux-gnu", "i486")
        if unsupported_pointer.returncode == 0 or "shared pointer" not in unsupported_pointer.stderr:
            raise RuntimeError("pointer-only gate accepted non-lock-free u64 target:\n" +
                               unsupported_pointer.stdout + unsupported_pointer.stderr)
        tiny_pointer = compile_c("#define __TINYC__ 1\n" + pointer_gates + "\nint probe;\n",
                                 "x86_64-unknown-linux-gnu")
        if tiny_pointer.returncode == 0 or "require GCC or Clang" not in tiny_pointer.stderr:
            raise RuntimeError("pointer-only gate accepted TinyCC:\n" +
                               tiny_pointer.stdout + tiny_pointer.stderr)

        # SharedPointer remains an unsupported public capability on MSVC, but
        # the separately compiled common runtime always includes its registry
        # implementation. Its internal reference-count primitives must
        # therefore select Interlocked operations rather than leave GCC-only
        # __atomic builtins in the MSVC path.
        runtime_text = (Path(__file__).parents[1] / "src" / "runtime" /
                        "runtime_threads.h").read_text()
        helpers = re.search(r"static void gs_shared_publish\(.*?"
                            r"(?=static GS_NORETURN void gs_shared_bad)",
                            runtime_text, re.S)
        if not helpers:
            raise RuntimeError("cannot find shared registry atomic helpers")
        helper_text = helpers[0]
        for token in ("__atomic_", "__ATOMIC_"):
            if runtime_text.count(token) != helper_text.count(token):
                raise RuntimeError("unguarded GCC atomic remains outside shared registry helpers: " +
                                   token)
        msvc_probe = ("#define _MSC_VER 1930\n"
                      "typedef unsigned long long uint64_t; typedef long long LONG64;\n"
                      "typedef struct { uint64_t generation; } gs_shared_record;\n"
                      "static LONG64 InterlockedExchange64(volatile LONG64 *p, LONG64 v) "
                      "{ LONG64 old = *p; *p = v; return old; }\n"
                      "static LONG64 InterlockedCompareExchange64(volatile LONG64 *p, LONG64 v, "
                      "LONG64 expected) { LONG64 old = *p; if (old == expected) *p = v; return old; }\n"
                      "static LONG64 InterlockedExchangeAdd64(volatile LONG64 *p, LONG64 v) "
                      "{ LONG64 old = *p; *p += v; return old; }\n" + helper_text +
                      "\nint probe(void) { gs_shared_record r = { 0 }; "
                      "gs_shared_publish(&r, 1); return (int)(gs_shared_ref_add(&r.generation) + "
                      "gs_shared_ref_sub(&r.generation) + gs_shared_ref_load(&r.generation)); }\n")
        msvc_helpers = compile_c(msvc_probe, "x86_64-unknown-linux-gnu")
        if msvc_helpers.returncode:
            raise RuntimeError("shared registry helpers fail in the MSVC branch:\n" +
                               msvc_helpers.stdout + msvc_helpers.stderr)
        preprocessed = subprocess.run([str(clang.cc), "-target", "x86_64-unknown-linux-gnu",
                                       "-ffreestanding", "-std=c11", "-E", "-P", "-x", "c", "-"],
                                      input=msvc_probe, capture_output=True, text=True, timeout=60)
        if preprocessed.returncode or "__atomic_" in preprocessed.stdout or "__ATOMIC_" in preprocessed.stdout:
            raise RuntimeError("MSVC shared registry path retains GCC atomic builtins:\n" +
                               preprocessed.stdout + preprocessed.stderr)
        queue_source = root / "pointer_queue_shutdown.goose"
        queue_source.write_text('fn main() { let p, o, ok = shared_pointer_alloc<i64>(7); '
                                'assert(ok && qput(p)); }\n')
        queue_c = root / "pointer_queue_shutdown.c"
        built = subprocess.run([str(exe), "-O2", "-o", str(queue_c), str(queue_source)],
                               capture_output=True, text=True, timeout=60)
        if built.returncode:
            raise RuntimeError(built.stdout + built.stderr)
        queue_text = queue_c.read_text()
        if not re.search(r"gs_qdestroy\(&gs_q_.*?, 1\);", queue_text):
            raise RuntimeError("pointer queue emitted no pointer-aware shutdown release")

        adopt_source = root / "pointer_queue_adopt.goose"
        adopt_source.write_text(
            'fn main() { let p, o, ok = shared_pointer_alloc<i64>(7); '
            'assert(ok && qput(p)); let a, got = qpoll<SharedPointer<i64>>(); '
            'assert(got); shared_pointer_release(a); '
            'let q, qo, qok = shared_pointer_alloc<i64>(9); '
            'assert(qok && qput(q)); let b = qget<SharedPointer<i64>>(); '
            'shared_pointer_release(b); assert(shared_close(o)); assert(shared_close(qo)); }\n')
        adopt_c = root / "pointer_queue_adopt.c"
        built = subprocess.run([str(exe), "-O2", "-o", str(adopt_c), str(adopt_source)],
                               capture_output=True, text=True, timeout=60)
        if built.returncode:
            raise RuntimeError(built.stdout + built.stderr)
        adopt_text = adopt_c.read_text()
        for operation in ("gs_qpoll", "gs_qget"):
            start = adopt_text.find(" = " + operation + "(")
            window = adopt_text[start:start + 1000] if start >= 0 else ""
            adopted, freed = window.find("gs_shared_pointer_adopt("), window.find("free(")
            if adopted < 0 or freed < 0 or adopted > freed:
                raise RuntimeError(operation +
                                   " does not adopt the pointer claim before freeing its queue node")
    return None
