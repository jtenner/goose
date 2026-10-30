// Audited native contract: snapshot/job storage is sealed before spawn;
// claim is atomic; each result slot has one writer and is read after all joins.
// Destruction belongs only to the coordinator. Integer handles are deliberate:
// their equality is accepted, and their resource lifetime remains an FFI duty.
extern fn contract_create() -> u64 main_thread_only;
extern fn contract_snapshot(handle: u64) -> i64 worker_callable;
extern fn contract_claim(handle: u64) -> i64 worker_callable;
extern fn contract_job(handle: u64, index: i64) -> i64 worker_callable;
extern fn contract_report(handle: u64, index: i64, value: i64) worker_callable;
extern fn contract_result(handle: u64, index: i64) -> i64 main_thread_only;
extern fn contract_destroy(handle: u64) main_thread_only;
struct Options { increment: i64 }
var options = Options { increment: 7 };
thread_fn worker(handle: u64, duplicate: u64) {
    assert(handle == duplicate);
    let count = contract_snapshot(handle);
    var scratch: i64[>..] = [];
    loop {
        let index = contract_claim(handle);
        if index >= count { break; }
        scratch.push(contract_job(handle, index) + options.increment);
        contract_report(handle, index, scratch[0]);
        scratch.clear();
    }
}
fn main() {
    let handle = contract_create();
    var ids: i64[>..] = [];
    for i in 4 { ids.push(thread_spawn(worker, handle, handle)); }
    for id in ids { assert(thread_wait(id)); }
    for index in 128 { assert(contract_result(handle, index) == index * 3 + 7); }
    contract_destroy(handle);
    print("worker native scheduler contract ok");
}
