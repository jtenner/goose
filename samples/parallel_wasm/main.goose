// Standalone native Wasm -> x86-64 compiler. Supported subset and protocol:
// README.md. Native build required; no application C sidecars/helpers.
import std;
import os;

let RECORD_BYTES: u64 = 40;
let MAX_FUNCTIONS: u64 = 100000;
let MAX_BODY: u64 = 4096;
struct Job { index: u32, offset: u64, length: u64, output: u64, capacity: u64 }

// Bounds use subtraction; every LEB is limited to five bytes and 32 bits.
fn uleb(a: SharedAccess, pos: u64&, end: u64) -> u64, bool {
    var value: u64 = 0;
    for i in 5 {
        if pos >= end { return 0, false; }
        let b = memory_read<u8>(a, pos, false);
        pos++;
        if i == 4 && b > 15 { return 0, false; }
        value |= ((b & 127) as u64) << (i * 7);
        if b < 128 { return value, true; }
    }
    return 0, false;
}
fn sleb32(a: SharedAccess, pos: u64&, end: u64) -> u32, bool {
    var value: i64 = 0;
    for i in 5 {
        if pos >= end { return 0, false; }
        let b = memory_read<u8>(a, pos, false);
        pos++;
        if i == 4 && ((b & 0x78) != 0 && (b & 0x78) != 0x78) { return 0, false; }
        value |= ((b & 127) as i64) << (i * 7);
        if b < 128 {
            if (b & 64) != 0 { value |= (-1 as i64) << ((i + 1) * 7); }
            return value as! u32, true;
        }
    }
    return 0, false;
}

// Only sections 1,3,10, in order, with one () -> i32 type. Unsupported
// sections are rejected, never skipped under a claim of full validation.
fn parse_module(a: SharedAccess, jobs: Job[>..]&) -> bool {
    let size = shared_size(a);
    if size < 8 { return false; }
    if memory_read<u32>(a, 0, false) != 0x6d736100 ||
       memory_read<u32>(a, 4, false) != 1 { return false; }
    var pos: u64 = 8;
    var last: u8 = 0;
    var typed = false;
    var functions: u64 = 0;
    var bodies: u64 = 0;
    var out: u64 = 0;
    while pos < size {
        let id = memory_read<u8>(a, pos, false); pos++;
        if id <= last || (id != 1 && id != 3 && id != 10) { return false; }
        last = id;
        let length, length_ok = uleb(a, pos, size);
        if !length_ok || length > size - pos { return false; }
        let end = pos + length;
        let count, count_ok = uleb(a, pos, end);
        if !count_ok || count > MAX_FUNCTIONS { return false; }
        if id == 1 {
            if count != 1 || end - pos != 4 { return false; }
            if memory_read<u32>(a, pos, false) != 0x7f010060 { return false; }
            pos = end;
            typed = true;
        } else if id == 3 {
            functions = count;
            if count > 0 && !typed { return false; }
            for i in count {
                let type_index, type_ok = uleb(a, pos, end);
                if !type_ok || type_index != 0 { return false; }
            }
        } else {
            bodies = count;
            if bodies != functions { return false; }
            for i in count {
                let n, n_ok = uleb(a, pos, end);
                if !n_ok || n == 0 || n > MAX_BODY || n > end - pos { return false; }
                let capacity = n * 6 + 32;
                jobs.push(Job { index: i as u32, offset: pos, length: n,
                                output: out, capacity: capacity });
                out += capacity;
                pos += n;
            }
        }
        if pos != end { return false; }
    }
    return bodies == functions;
}

// This emits instructions, not folded constants or an interpreter result.
// x86-64 machine stack holds zero-extended i32 values; addition wraps in eax.
fn compile_body(a: SharedAccess, offset: u64, length: u64, code: u8[>..]&) -> bool {
    if offset > shared_size(a) || length > shared_size(a) - offset { return false; }
    var pos = offset;
    let end = offset + length;
    let locals, locals_ok = uleb(a, pos, end);
    if !locals_ok || locals != 0 { return false; }
    var depth: i64 = 0;
    while pos < end {
        let op = memory_read<u8>(a, pos, false); pos++;
        if op == 0x41 {
            let value, ok = sleb32(a, pos, end);
            if !ok || depth >= 128 { return false; }
            code.push(0xb8); // mov eax, imm32
            for i in 4 { code.push((value >> (i * 8)) as! u8); }
            code.push(0x50); // push rax
            depth++;
        } else if op == 0x6a {
            if depth < 2 { return false; }
            code.append([0x59, 0x58, 0x01, 0xc8, 0x50]);
            depth--;
        } else if op == 0x0b || op == 0x0f {
            if depth != 1 { return false; }
            if op == 0x0f {
                if pos >= end || memory_read<u8>(a, pos, false) != 0x0b { return false; }
                pos++;
            }
            if pos != end { return false; }
            code.append([0x58, 0xc3]);
            return true;
        } else { return false; }
    }
    return false;
}

fn compile_jobs(module: SharedView, table: SharedView, output: SharedView,
                statuses: SharedView, next: SharedAtomicU64, cancel: SharedAtomicU32,
                start: SharedAtomicU32, count: u64, inject_abort: bool) {
    while atomic_load(start, "Acquire") == 0 {}
    let input = shared_borrow(module); // concurrent readonly borrows
    loop {
        if atomic_load(cancel, "Acquire") != 0 { break; }
        let i = atomic_fetch_add(next, 1, "Relaxed"); // unique, mutex-free claim
        if i >= count { break; }
        let status = shared_atomic_view_u32(statuses, i);
        atomic_store(status, 1, "Release"); // RUNNING, parent recovers after abort
        let record = shared_borrow(table, i * RECORD_BYTES, RECORD_BYTES);
        assert(memory_read<u32>(record, 0, false) == i);
        let offset = memory_read<u64>(record, 8, false);
        let length = memory_read<u64>(record, 16, false);
        let out = memory_read<u64>(record, 24, false);
        let capacity = memory_read<u64>(record, 32, false);
        shared_release(record);
        let dest = shared_borrow(output, out, capacity);
        let visits = memory_read<u32>(dest, 8, false);
        memory_write<u32>(dest, 8, visits + 1, false); // oracle detects duplicate claims
        if inject_abort && i == 0 { abort("injected worker compile abort"); }
        var code: u8[>..] = [];
        let ok = compile_body(input, offset, length, code);
        if ok {
            assert((code.len as u64) <= capacity - 16);
            memory_write<u64>(dest, 0, code.len as u64, false);
            for k in code.len { memory_write<u8>(dest, 16 + k as u64, code[k], false); }
        }
        shared_release(dest);
        atomic_store(status, if ok { 2 } else { 3 }, "Release");
    }
    shared_release(input);
}
thread_fn worker(module: SharedView, table: SharedView, output: SharedView,
                 statuses: SharedView, next: SharedAtomicU64, cancel: SharedAtomicU32,
                 start: SharedAtomicU32, count: u64, inject_abort: bool) {
    compile_jobs(module, table, output, statuses, next, cancel, start, count, inject_abort);
}
thread_fn misuse(v: SharedView, kind: i64) {
    if kind == 0 { shared_borrow(v, shared_size(v), 1); }
    let a = shared_borrow(v);
    if kind == 1 { memory_read<u64>(a, shared_size(a) - 1, false); }
    if kind == 2 { shared_release(a); memory_read<u8>(a, 0, false); }
    if kind == 3 { memory_write<u8>(a, 0, 0, false); }
}
thread_fn stale() {
    let o, ok = shared_alloc(64); assert(ok);
    let v = shared_view(o, 0, 64);
    assert(shared_close(o));
    shared_borrow(v);
}
fn fault_tests(module: SharedView) {
    let invalid, ok = shared_alloc(18446744073709551615);
    assert(!ok && !shared_close(invalid));
    let owner, yes = shared_alloc(64); assert(yes);
    let view = shared_view(owner, 0, 64);
    for kind in 3 { assert(!thread_wait(thread_spawn_contained(misuse, view, kind))); }
    assert(!thread_wait(thread_spawn_contained(misuse, module, 3)));
    assert(!thread_wait(thread_spawn_contained(stale)));
    let a = shared_borrow(view);
    assert(!shared_close(owner));
    shared_release(a);
    assert(shared_close(owner) && !shared_close(owner));
    print("faults ok");
}
fn fail(message: u8[:]) { write_stderr(message); write_stderr("\n"); exit(1); }
fn main() {
    let argv = args();
    if argv.len != 5 { fail("usage: wasm module.wasm size workers(0=serial) normal|abort|cancel|faults"); }
    let size, size_ok = parse_int(argv[2]);
    let workers, workers_ok = parse_int(argv[3]);
    if !size_ok || size < 8 || size > 268435456 || !workers_ok || workers < 0 || workers > 64 {
        fail("invalid size or worker count");
    }
    let mode = argv[4];
    if mode != "normal" && mode != "abort" && mode != "cancel" && mode != "faults" { fail("invalid mode"); }
    if mode == "abort" && workers == 0 { fail("abort requires contained workers"); }
    let mapped, mapped_ok = shared_map_readonly(argv[1], size as u64);
    if !mapped_ok { fail("cannot map module"); }
    let module = shared_view(mapped, 0, size as u64);
    let input = shared_borrow(module);
    var jobs: Job[>..] = [];
    let valid = parse_module(input, jobs);
    shared_release(input);
    if !valid { assert(shared_close(mapped)); fail("malformed or unsupported Wasm module"); }
    if mode == "faults" { fault_tests(module); assert(shared_close(mapped)); return; }
    let count = jobs.len as u64;
    let table_owner, table_ok = shared_alloc(max(1, count * RECORD_BYTES));
    if !table_ok { assert(shared_close(mapped)); fail("work table allocation failed"); }
    var output_size: u64 = 1;
    if count > 0 { let last = jobs[jobs.len - 1]; output_size = last.output + last.capacity; }
    let out_owner, out_ok = shared_alloc(output_size);
    if !out_ok { assert(shared_close(table_owner)); assert(shared_close(mapped)); fail("output allocation failed"); }
    let ctl_owner, ctl_ok = shared_alloc(32 + max(1, count) * 4);
    if !ctl_ok {
        assert(shared_close(out_owner)); assert(shared_close(table_owner)); assert(shared_close(mapped));
        fail("control allocation failed");
    }
    let table = shared_view(table_owner, 0, max(1, count * RECORD_BYTES));
    let output = shared_view(out_owner, 0, output_size);
    let init = shared_borrow(table);
    for job in jobs {
        let p = job.index * RECORD_BYTES;
        memory_write<u32>(init, p, job.index, false);
        memory_write<u64>(init, p + 8, job.offset, false);
        memory_write<u64>(init, p + 16, job.length, false);
        memory_write<u64>(init, p + 24, job.output, false);
        memory_write<u64>(init, p + 32, job.capacity, false);
    }
    shared_release(init);
    let next = shared_atomic_u64(ctl_owner, 0, 0);
    let cancel = shared_atomic_u32(ctl_owner, 8, 0);
    let start = shared_atomic_u32(ctl_owner, 12, 0);
    let statuses = shared_atomic_array_u32(ctl_owner, 32, max(1, count), 0);
    if mode == "cancel" { atomic_store(cancel, 1, "Release"); }
    var ids: i64[>..] = [];
    for w in workers {
        ids.push(thread_spawn_contained(worker, module, table, output, statuses, next, cancel, start, count, mode == "abort"));
    }
    if workers > 0 {
        // Every worker is waiting for start with pre-spawn leases already held.
        assert(!shared_close(mapped));
        assert(!shared_close(table_owner) && !shared_close(out_owner) && !shared_close(ctl_owner));
    }
    atomic_store(start, 1, "Release");
    if workers == 0 { compile_jobs(module, table, output, statuses, next, cancel, start, count, false); }
    var failed: u64 = 0;
    for id in ids { if !thread_wait(id) { failed++; } }
    // Shutdown has joined EVERY worker before inspecting output or closing any owner.
    let results = shared_borrow(output);
    let hex = "0123456789abcdef";
    var claimed: u64 = 0;
    for job in jobs {
        let flag = shared_atomic_view_u32(statuses, job.index as u64);
        var status = atomic_load(flag, "Acquire"); // publication before result reads
        if status == 1 { // contained abort left a RUNNING job
            status = 4; atomic_store(flag, status, "Release");
        }
        if status == 0 { // shutdown or last worker failed
            status = 5; atomic_store(flag, status, "Release");
        }
        let visits = memory_read<u32>(results, job.output + 8, false);
        claimed += visits;
        let n = memory_read<u64>(results, job.output, false);
        assert(n <= job.capacity - 16);
        var text: u8[>..] = [];
        for k in n {
            let b = memory_read<u8>(results, job.output + 16 + k, false);
            text.push(hex[b >> 4]); text.push(hex[b & 15]);
        }
        print("job ", job.index, " ", status, " ", visits, " ", text);
    }
    shared_release(results);
    assert(shared_close(ctl_owner)); assert(shared_close(out_owner));
    assert(shared_close(table_owner)); assert(shared_close(mapped));
    print("summary ", count, " ", claimed, " ", failed);
}
