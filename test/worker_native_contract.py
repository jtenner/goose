"""Strict worker FFI boundary: checked graphs, exact declarations and escapes."""
from pathlib import Path
import toolchain as tc


def check_worker_native_contract(exe, base, cc=None, *, runtime=None, extra=()):
    base = (Path(base) / "worker-native-contract").resolve()
    base.mkdir(parents=True, exist_ok=True)
    failures = []

    def check(name, text, want=(), *, strict=True, success=False, roundtrip=False):
        source = base / (name + ".goose")
        tc.write_text(source, text)
        flags = ["--strict-worker-native"] if strict else []
        code, out, err = tc.run_capture([exe, *flags, "--roundtrip" if roundtrip else "--check", "--check", source])
        tc.write_text(base / (name + ".log"), out + err)
        if (code == 0) != success or any(word not in out + err for word in want):
            failures.append(f"{name}: exit {code}; expected {'accept' if success else repr(want)}\n{out}{err}")
        return source

    # These need no new syntax: with only flag plumbing they must fail red
    # because the old checker accepts both unclassified externs and raw pointers.
    decl = "extern fn native() -> i64;\n"
    cases = {
        "direct": ("thread_fn worker() { native(); }", ["worker -> native"]),
        "helper": ("fn helper() { native(); } thread_fn worker() { helper(); }", ["worker -> helper -> native"]),
        "generic": ("fn helper<T>(x: T) { native(); } thread_fn worker() { helper(1); }", ["worker -> helper -> native"]),
        "recursive": ("recursive fn helper(n: i64) { if n > 0 { helper(n - 1); } native(); } thread_fn worker() { helper(2); }", ["worker -> helper -> native"]),
        "bound": ("fn invoke<F>() { F(); } fn helper() { native(); } thread_fn worker() { invoke(helper); }", ["worker -> invoke -> helper -> native"]),
        "format": ("struct Show { x: i64 } fn format(out: u8[>..]&, x: Show) { native(); out.append(\"ok\"); } thread_fn worker() { print(Show { x: 1 }); }", ["worker -> format -> native"]),
        "dispatch": ("enum E { A { x: i64 }, B { y: i64 } } fn visit(x: E.A) { native(); } fn visit(x: E.B) {} thread_fn worker(x: E) { visit(x); }", ["worker -> visit -> native"]),
    }
    for name, (body, path) in cases.items():
        main = "fn main() { thread_wait(thread_spawn(worker" + (", E.A { x: 1 }" if name == "dispatch" else "") + ")); }"
        text = decl + body + main
        check(name, text, ["unclassified extern", "declaration at", *path])
        check(name + "-legacy", text, strict=False, success=True)

    unsafe = {
        "unsafe_ptr_from_handle": "unsafe_ptr_from_handle(1)",
        "unsafe_handle_from_ptr": "unsafe_handle_from_ptr(unsafe_ptr_from_handle(1))",
        "unsafe_ptr_add": "unsafe_ptr_add(unsafe_ptr_from_handle(1), 1)",
        "unsafe_load": "unsafe_load<u64>(unsafe_ptr_from_handle(1), false)",
        "unsafe_store": "unsafe_store<u64>(unsafe_ptr_from_handle(1), 1, false)",
    }
    for name, expr in unsafe.items():
        text = f"fn helper() {{ {expr}; }} thread_fn worker() {{ helper(); }} fn main() {{ thread_wait(thread_spawn(worker)); }}"
        check(name, text, ["unsafe native operation", "worker -> helper -> " + name])
        check(name + "-legacy", text, strict=False, success=True)

    text = "fn helper(address: u64) { unsafe_ptr_from_handle(address); } thread_fn worker(address: u64) { helper(address); } fn main() { thread_wait(thread_spawn(worker, 1)); }"
    check("integer-address", text, ["unsafe native operation", "worker -> helper -> unsafe_ptr_from_handle"])
    check("integer-address-legacy", text, strict=False, success=True)
    check("main-only", "extern fn native() main_thread_only; thread_fn worker() { native(); } fn main() { thread_wait(thread_spawn(worker)); }",
          ["main-thread-only extern", "worker -> native", "declaration at"])
    check("main-only-legacy", "extern fn native() main_thread_only; thread_fn worker() { native(); } fn main() { thread_wait(thread_spawn(worker)); }",
          ["runs on the main thread only", "worker -> native"], strict=False)
    check("overload", "extern fn native(x: i64) worker_callable; extern fn native(x: bool); thread_fn worker() { native(1); native(true); } fn main() { thread_wait(thread_spawn(worker)); }",
          ["unclassified extern", "worker -> native", "declaration at"])
    check("unused", "extern fn native(); fn helper() { native(); } thread_fn worker() {} fn main() { thread_wait(thread_spawn(worker)); }", success=True)
    check("exact", "extern fn allowed() worker_callable; extern fn native(); thread_fn worker() { allowed(); native(); } fn main() { thread_wait(thread_spawn(worker)); }",
          ["unclassified extern", "worker -> native"])
    check("static-views", 'let label: const u8[:] = "readonly"; thread_fn worker() { print(label); } fn main() { thread_wait(thread_spawn(worker)); }', success=True)
    check("inactive", "extern fn native(); thread_fn worker() { const if false { native(); unsafe_ptr_from_handle(1); } } fn main() { thread_wait(thread_spawn(worker)); }", success=True)
    check("coordinator", "extern fn native() main_thread_only; thread_fn worker() {} fn main() { native(); thread_wait(thread_spawn(worker)); }", success=True, roundtrip=True)
    check("annotated", "extern fn native() worker_callable = \"contract_native\"; thread_fn worker() { native(); } fn main() { thread_wait(thread_spawn(worker)); }", success=True, roundtrip=True)
    check("dylib", 'extern "contract-library" { fn native() worker_callable; } thread_fn worker() { native(); } fn main() { thread_wait(thread_spawn(worker)); }', success=True, roundtrip=True)
    check("conflicting", "extern fn native() worker_callable main_thread_only; fn main() {}", ["only one worker-native classification"])
    # A worker-callable member cannot waive a package's existing restriction.
    tc.write_text(base / "restricted.goose", "extern fn native() worker_callable;\n")
    tc.write_text(base / "package.build", "main_thread_only = true;\n")
    check("package", 'import .restricted; thread_fn worker() { native(); } fn main() { thread_wait(thread_spawn(worker)); }', ["main-thread-only extern", "worker -> native"])

    if failures:
        raise RuntimeError("\n".join(failures))

    source = tc.REPO_ROOT / "test" / "threads" / "native_contract" / "scheduler.goose"
    native = source.with_suffix(".c")
    text = source.read_text()
    # The same scheduler is rejected until its worker declarations are audited.
    check("scheduler-unclassified", text.replace(" worker_callable", ""),
          ["unclassified extern", "worker -> contract_snapshot"])
    check("scheduler", text, success=True, roundtrip=True)
    for goose_level in (0, 2):
        cfile = base / f"scheduler-g{goose_level}.c"
        code, out, err = tc.run_capture([exe, "--strict-worker-native", f"-O{goose_level}", "-o", cfile, source])
        if code:
            raise RuntimeError(out + err)
        if cc:
            for debug in (False, True):
                binary = base / (f"scheduler-g{goose_level}-d{int(debug)}" + tc.EXE_SUFFIX)
                ok, log = cc.compile([cfile, native], binary, opt=goose_level, extra=extra,
                                     defines=["GS_DEBUG=1"] if debug else [],
                                     strict_decls=True, runtime=runtime)
                if not ok:
                    raise RuntimeError(log)
                code, out, err = tc.run_capture([binary])
                if code or tc.sanitizer_failure(err) or out.strip() != "worker native scheduler contract ok":
                    raise RuntimeError(f"scheduler exit {code}\n{out}{err}")
    if failures:
        raise RuntimeError("\n".join(failures))

    # The setting must reach editor analyses as well as the CLI compiler.
    from lsp_protocol import Client, uri_of
    source = base / "direct.goose"
    client = Client(exe, base, ["--strict-worker-native"])
    try:
        client.request("initialize", {"processId": None, "rootUri": uri_of(base),
                                      "capabilities": {},
                                      "initializationOptions": {"entryFiles": [str(source)]}})
        client.send("initialized", {}, request=False)
        client.send("textDocument/didOpen", {"textDocument": {
            "uri": uri_of(source), "languageId": "goose", "version": 1,
            "text": source.read_text()}}, request=False)
        diagnostics = client.diagnostics_for(uri_of(source))
        if not any("worker -> native" in d["message"] and "unclassified extern" in d["message"]
                   for d in diagnostics):
            raise RuntimeError("strict LSP analysis lost the contract: " + repr(diagnostics))
        client.request("shutdown", None)
        client.send("exit", request=False)
        if client.p.wait(timeout=30):
            raise RuntimeError("strict LSP shutdown failed")
    finally:
        if client.p.poll() is None:
            client.p.kill()
            client.p.wait()

    for verb in ("check", "build", "run"):
        code, out, err = tc.run_capture([exe, verb, "--strict-worker-native", source])
        if code == 0 or "worker -> native" not in out + err:
            raise RuntimeError(f"{verb} lost strict checking:\n{out}{err}")
    # Existing shared capability/atomic programs remain permitted under strict mode.
    for fixture in ("memory/shared_atomics", "threads/thread_globals",
                    "threads/thread_resizable_arguments",
                    "threads/thread_sync_contract"):
        source = tc.REPO_ROOT / "test" / (fixture + ".goose")
        code, out, err = tc.run_capture([exe, "check", "--strict-worker-native", source])
        if code:
            raise RuntimeError("existing isolated/capability program rejected:\n" + out + err)
