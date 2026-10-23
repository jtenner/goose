#!/usr/bin/env python3
"""Self-contained library headers, public ABI, and safe-capability rejection.

Called by run_tests.py; the standalone entry point also supports a focused
GCC/Clang matrix with full ASan/UBSan/alignment. Generated artifacts and exact
subprocess results remain under build/gen/library-headers/<toolchain>.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import toolchain as tc


def check_library_headers(exe, cc, base, *, extra=()):
    base = (Path(base) / "library-headers" / cc.name).resolve()
    base.mkdir(parents=True, exist_ok=True)
    results, failures = [], []
    env = dict(os.environ)
    # GCC must use its own assembler/linker with an independently installed
    # Clang first on PATH. This also applies to generated-program links.
    flags = list(extra)
    if cc.name == "gcc" and sys.platform.startswith("linux"):
        flags += ["-B/usr/bin/"]

    def run(argv, *, expected=0, diagnostic=None):
        argv = [str(a) for a in argv]
        p = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True,
                           text=True, errors="replace", timeout=120)
        output = p.stdout + p.stderr
        good = (p.returncode == expected and
                (diagnostic is None or diagnostic in output) and
                not tc.sanitizer_failure(output))
        results.append(dict(command=argv, returncode=p.returncode,
                            stdout=p.stdout, stderr=p.stderr, passed=good))
        if not good:
            failures.append(" ".join(argv) + "\n" + output)
        return good

    common = '''
#include "HEADER"
#include "HEADER"
#include <assert.h>
#include <stddef.h>
#include <string.h>
#ifdef __cplusplus
#define STATIC_ASSERT static_assert
#else
#define STATIC_ASSERT _Static_assert
#endif
struct PackingProbe { uint8_t prefix; uint64_t word; };
STATIC_ASSERT(offsetof(struct PackingProbe, word) > 1, "header restores packing");
'''
    bodies = {
        "public": '''
STATIC_ASSERT(sizeof(ApiPacked_g) == 9, "packed nested layout");
STATIC_ASSERT(offsetof(ApiPacked_g, inner_g) == 1, "packed nested offset");
STATIC_ASSERT(offsetof(ApiPacked_g, values_g) == 5, "packed array offset");
STATIC_ASSERT(sizeof(ApiRefOnly_g) == 4, "complete reference pointee");
STATIC_ASSERT(sizeof(ApiSliceOnly_g) == 4, "complete slice element");
int main(int argc, char **argv) {
    goose_init(argc, argv); goose_init(argc, argv);
    assert(api() == 42);
    double (*s)(int32_t, double, uint8_t) = scalar;
    assert(s(20, 21.0, 1) == 42.0);
    ApiPacked_g p = { 1, { 42 }, { { 2, 3 } } };
    ApiPacked_g (*copy)(ApiPacked_g) = packed;
    p = copy(p); assert(p.prefix_g == 1 && p.inner_g.value_g == 42);
    assert(p.values_g.e[0] == 2 && p.values_g.e[1] == 3);
    ApiRefOnly_g r = { 42 };
    uint32_t (*ref)(ApiRefOnly_g *) = reference;
    assert(ref(&r) == 42);
    ApiSliceOnly_g e = { 42 };
    sl_ApiSliceOnly_g xs = { &e, 1 };
    uint32_t (*slice)(sl_ApiSliceOnly_g) = slices;
    assert(slice(xs) == 42);
    ApiChoice_g c = { 0 };
    c.tag = ApiChoice_g_Some_g_k; c.u.v_Some_g.value_g = 42;
    c = choose(c); assert(c.u.v_Some_g.value_g == 42);
    int64_t n = 0;
    const uint8_t *(*bytes)(int64_t *) = text;
    const uint8_t *t = bytes(&n);
    assert(n == 6 && memcmp(t, "header", 6) == 0);
    return 0;
}
''',
        "public_raw": '''
STATIC_ASSERT(sizeof(gs_unsafe_ptr) == sizeof(void *), "raw pointer ABI");
int main(int argc, char **argv) {
    goose_init(argc, argv);
    uint64_t value = 42;
    gs_unsafe_ptr p = &value;
    void *(*direct)(void *) = pointer;
    assert(direct(p) == &value);
    assert(pointer_ref(&p) == &value);
    sl_UnsafePtr xs = { &p, 1 };
    assert(pointer_slice(xs) == &value);
    return 0;
}
''',
    }
    scalar_body = '''
int main(int argc, char **argv) {
    goose_init(argc, argv); goose_init(argc, argv);
    uint32_t (*entry)(void) = api;
    assert(entry() == 42);
    return 0;
}
'''
    try:
        for level in (0, 2):
            for source in sorted((ROOT / "test/library_headers/fixtures").glob("*.goose")):
                # UnsafePtr explicitly requires GCC/Clang typedef alignment.
                if cc.style == "msvc" and source.stem.endswith("raw"):
                    continue
                stem = f"{source.stem}-g{level}"
                cfile, header = base / f"{stem}.c", base / f"{stem}.h"
                if not run([exe, f"-O{level}", "--standalone", "--header", header,
                            source, "-o", cfile]):
                    continue
                decls = header.read_text(encoding="utf-8")
                # Private implementation types are not part of the API.
                if any(n in decls for n in ("gs_shared_cap", "gs_shared_atomic_cap",
                                            "Private", "Box_g")):
                    failures.append(f"{header}: private implementation types leaked")
                if source.stem == "private_raw" and "gs_unsafe_ptr" in decls:
                    failures.append(f"{header}: private UnsafePtr leaked")
                obj = base / f"{stem}.o"
                compile_flags = (["/nologo", "/c", f"/Fo:{obj}"] if cc.style == "msvc" else
                                 ["-std=c11", f"-O{level}", "-c", "-o", obj])
                ok = run([cc.cc, *compile_flags, *flags, cfile])
                host_text = common.replace("HEADER", header.name)
                for suffix, cpp in (("c", False), ("cpp", True)):
                    if cpp and not cc.cxx:
                        continue
                    host = base / f"{stem}-host.{suffix}"
                    tc.write_text(host, host_text + bodies.get(source.stem, scalar_body))
                    # Inclusion is independent of whether generated C links.
                    driver = cc.cxx if cpp else cc.cc
                    syntax = (["/nologo", "/Zs"] if cc.style == "msvc" else
                              ["-std=c++17" if cpp else "-std=c11", "-fsyntax-only"])
                    if not run([driver, *syntax, *flags, host]) or not ok:
                        continue
                    binary = base / f"{stem}-{suffix}{tc.EXE_SUFFIX}"
                    link_flags = (["/nologo", f"/Fe:{binary}", f"/Fo:{base}{os.sep}"]
                                  if cc.style == "msvc" else
                                  ["-std=c++17" if cpp else "-std=c11", f"-O{level}",
                                   "-o", binary])
                    libs = ([] if tc.IS_WINDOWS else ["-lm", "-pthread"] +
                            (["-ldl"] if sys.platform.startswith("linux") else []))
                    if run([driver, *link_flags, *flags, host, obj, *libs]):
                        run([binary])

            # Rejection must be a normal frontend error, never a C failure or
            # crash. Cover all five kinds directly and inside public shapes.
            for kind in ("SharedOwner", "SharedView", "SharedAccess",
                         "SharedAtomicU32", "SharedAtomicU64"):
                for shape in (kind, kind + "&", kind + "[:]", "Hidden", "Hidden&", "Hidden[1]"):
                    for boundary in ("export", "extern"):
                        name = f"reject-{kind}-{len(results)}.goose"
                        source = base / name
                        body = " {}" if boundary == "export" else ";"
                        tc.write_text(source, f"struct Hidden {{ value: {kind} }}\n"
                                      f"{boundary} fn reject(value: {shape}){body}\nfn main() {{}}\n")
                        run([exe, f"-O{level}", "--check", source], expected=1,
                            diagnostic="cannot cross to C")
                source = base / f"reject-return-{kind}.goose"
                tc.write_text(source, f"extern fn reject() -> {kind};\nfn main() {{}}\n")
                run([exe, f"-O{level}", "--check", source], expected=1,
                    diagnostic="safe native capabilities have no raw C ABI")
                value = {
                    "SharedOwner": "owner",
                    "SharedView": "shared_view(owner, 0, 16)",
                    "SharedAccess": "shared_borrow(shared_view(owner, 0, 16))",
                    "SharedAtomicU32": "shared_atomic_u32(owner, 0, 42)",
                    "SharedAtomicU64": "shared_atomic_u64(owner, 0, 42)",
                }[kind]
                tc.write_text(source, f"export fn reject() -> {kind} {{\n"
                              f"let owner, ok = shared_alloc(16); assert(ok); {value}\n}}\n")
                run([exe, f"-O{level}", "--check", source], expected=1,
                    diagnostic="safe native capabilities have no raw C ABI")
    finally:
        tc.write_text(base / "commands.json", json.dumps(results, indent=2) + "\n")
    if failures:
        raise RuntimeError("\n".join(failures))
    return len(results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", default=ROOT / "build/goose", type=Path)
    parser.add_argument("--cc", choices=("gcc", "clang"), required=True)
    parser.add_argument("--sanitize", action="store_true")
    args = parser.parse_args()
    flags = (["-g", "-fsanitize=address,undefined,alignment",
              "-fno-sanitize-recover=all", "-fno-omit-frame-pointer"] if args.sanitize else [])
    checks = check_library_headers(args.exe.resolve(), tc.test_cc(args.cc), ROOT / "build/gen",
                                   extra=flags)
    print(f"library headers ({args.cc}): {checks} subprocess checks passed")
