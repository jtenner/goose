// Benchmark workload only. Timing is coordinated by run.py --run.
import std;
import os;

struct CheckState {
    value: u64,
    const if build::CHECK_REGISTER_CLOBBERS { register_owners: u64[2], } else {},
}
fn checked_emit(s: CheckState&, value: u64) {
    const if build::CHECK_REGISTER_CLOBBERS {
        if s.register_owners[0] != 0 { abort("REGISTER_CLOBBER_SENTINEL"); }
        s.register_owners[0] = value + 1;
    }
    s.value += value;
    const if build::CHECK_REGISTER_CLOBBERS {
        if s.register_owners[0] != value + 1 { abort("REGISTER_CLOBBER_SENTINEL"); }
        s.register_owners[0] = 0;
    }
}
thread_fn atomic_worker(slots: SharedView, next: SharedAtomicU64, count: u64,
                        index: u64, mode: i64) {
    if mode == 2 {
        loop { let job = atomic_fetch_add(next, 1, "Relaxed"); if job >= count { break; } }
    } else {
        let token = shared_atomic_view_u64(slots, if mode == 0 { index } else { 0 });
        for i in count { atomic_fetch_add(token, 1, "Relaxed"); }
    }
}
thread_fn empty() {}
thread_fn producer(data: SharedView, flag: SharedAtomicU64, count: u64) {
    for i in count {
        while atomic_load(flag, "Acquire") != 0 {}
        let a = shared_borrow(data);
        memory_write<u64>(a, 0, i + 1, false);
        shared_release(a);
        atomic_store(flag, 1, "Release");
    }
}
thread_fn consumer(data: SharedView, flag: SharedAtomicU64, count: u64) {
    for i in count {
        while atomic_load(flag, "Acquire") != 1 {}
        let a = shared_borrow(data);
        assert(memory_read<u64>(a, 0, false) == i + 1);
        shared_release(a);
        atomic_store(flag, 0, "Release");
    }
}
fn main() {
    let argv = args();
    assert(argv.len == 5);
    let which = argv[1];
    let n_arg, n_ok = parse_int(argv[2]);
    let w_arg, w_ok = parse_int(argv[3]);
    assert(n_ok && n_arg > 0 && w_ok && w_arg > 0 && w_arg <= 8);
    let n = n_arg as u64;
    let workers = w_arg as u64;
    let owner, ok = shared_alloc(1048576); assert(ok);
    let data = shared_view(owner, 0, 524288);
    let target = shared_view(owner, 524288, 524288);
    let controls, controls_ok = shared_alloc(128); assert(controls_ok);
    let next = shared_atomic_u64(controls, 0, 0);
    let slots = shared_atomic_array_u64(controls, 8, 8, 0);
    var operations: u64 = n;
    var checksum: u64 = 0;
    let t0 = clock();
    if which == "atomics_uncontended" || which == "atomics_contended" || which == "claims" {
        let mode = if which == "claims" { 2 } else if which == "atomics_uncontended" { 0 } else { 1 };
        var ids: i64[>..] = [];
        for w in workers { ids.push(thread_spawn(atomic_worker, slots, next, n, w, mode)); }
        for id in ids { assert(thread_wait(id)); }
        operations = if mode == 2 { n } else { n * workers };
        checksum = if mode == 2 { atomic_load(next, "Relaxed") } else { atomic_load(shared_atomic_view_u64(slots, 0), "Relaxed") };
    } else if which == "publication" {
        operations = min(n, 10000);
        let p = thread_spawn(producer, data, next, operations);
        let c = thread_spawn(consumer, data, next, operations);
        assert(thread_wait(p) && thread_wait(c));
        checksum = operations;
    } else if which == "scheduling" {
        let rounds = max(1, n / 1000);
        operations = rounds * workers;
        for r in rounds {
            var ids: i64[>..] = [];
            for w in workers { ids.push(thread_spawn(empty)); }
            for id in ids { assert(thread_wait(id)); }
        }
        checksum = operations;
    } else if which == "mmap" {
        operations = 64;
        for i in operations {
            let mapped, mapped_ok = shared_map_readonly(argv[4], 16777216); assert(mapped_ok);
            checksum += shared_size(mapped);
            assert(shared_close(mapped));
        }
    } else if which == "copy" {
        let src = shared_borrow(data);
        let dst = shared_borrow(target);
        let loops = max(1, n / 512);
        for i in loops { memory_copy(dst, 0, src, 0, 524288); }
        operations = loops * 524288;
        checksum = memory_read<u64>(dst, 0, false);
        shared_release(dst); shared_release(src);
    } else if which == "checks_disabled" || which == "checks_enabled" {
        var s = CheckState { value: 0,
            const if build::CHECK_REGISTER_CLOBBERS { register_owners: [0, 0], } else {},
        };
        for i in n { checked_emit(s, i & 65535); }
        checksum = s.value;
    } else {
        let a = shared_borrow(data);
        // Dependency chain for read latency; distinct streams for throughput.
        for i in 8192 { memory_write<u64>(a, i * 8, (i + 1) as u64 % 8192, false); }
        if which == "scalar_read_latency" {
            for i in n { checksum = memory_read<u64>(a, checksum * 8, false); }
        } else if which == "scalar_write_latency" {
            for i in n {
                memory_write<u64>(a, 0, checksum + 1, false);
                checksum = memory_read<u64>(a, 0, false);
            }
        } else if which == "scalar_read_throughput" {
            for i in n {
                let off = (i & 2047) * 8;
                checksum += memory_read<u64>(a, off, false) + memory_read<u64>(a, off + 16384, false)
                          + memory_read<u64>(a, off + 32768, false) + memory_read<u64>(a, off + 49152, false);
            }
            operations = n * 4;
        } else {
            assert(which == "scalar_write_throughput");
            for i in n {
                let off = (i & 2047) * 8;
                memory_write<u64>(a, off, i, false); memory_write<u64>(a, off + 16384, i, false);
                memory_write<u64>(a, off + 32768, i, false); memory_write<u64>(a, off + 49152, i, false);
            }
            operations = n * 4;
            checksum = memory_read<u64>(a, ((n - 1) & 2047) * 8, false);
        }
        shared_release(a);
    }
    let elapsed = clock() - t0;
    assert(shared_close(controls) && shared_close(owner));
    // Decimal seconds, work units, checksum. RSS is collected by the harness.
    var report: u8[>..] = [];
    format_flt(report, elapsed, 9);
    format(report, " ", operations, " ", checksum);
    print(report);
}
