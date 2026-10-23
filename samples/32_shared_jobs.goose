// no-jit: native shared atomics require GCC or Clang.
// Build: goose build samples/32_shared_jobs.goose --cc gcc
// One atomic claim counter, a typed completion table, and disjoint result
// ranges. Claims/status use inline native atomics; ordinary result access
// uses checked scoped range borrows outside the claim operation.
let JOBS = 1000;
thread_fn work(next: SharedAtomicU32, statuses: SharedView, results: SharedView) {
    loop {
        let job = atomic_fetch_add(next, 1, "Relaxed");
        if job >= JOBS { break; }
        let output = shared_borrow(results, job * 8, 8);
        memory_write<u64>(output, 0, (job + 1) as u64, false);
        shared_release(output);
        atomic_store(shared_atomic_view_u32(statuses, job), 1, "Release");
    }
}
fn main() {
    let owner, ok = shared_alloc(64 + JOBS * 12); assert(ok);
    let next = shared_atomic_u32(owner, 0, 0);
    let statuses = shared_atomic_array_u32(owner, 64, JOBS, 0);
    let results = shared_view(owner, 64 + JOBS * 4, JOBS * 8);
    var workers: i64[>..] = [];
    for i in 4 { workers.push(thread_spawn(work, next, statuses, results)); }
    for id in workers { assert(thread_wait(id)); }
    let output = shared_borrow(results);
    var sum: u64 = 0;
    for job in JOBS {
        assert(atomic_load(shared_atomic_view_u32(statuses, job), "Acquire") == 1);
        sum += memory_read<u64>(output, job * 8, false);
    }
    shared_release(output); assert(shared_close(owner));
    print(JOBS, " jobs, sum ", sum);
}
