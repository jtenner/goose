// Spawn snapshots precede execution: the gate forces main's later mutation
// to happen before the worker observes its private global through helpers.
var option = 0;
struct Gate { token: i64 }
struct Result { value: i64, bytes: u8[] }
struct Show { unused: i64 }
fn read_option() -> i64 { option }
fn nested_option() -> i64 { read_option() }
fn format(out: u8[>..]&, item: Show) { out.append(str(nested_option())); }
thread_fn snapshot() {
    qget<Gate>();
    var scratch: u8[>..] = str(Show { unused: 0 });
    qput(Result { value: nested_option(), bytes: copy(scratch) });
    option = -1;
    scratch.clear();
}
thread_fn contained(fail: bool) { if fail { abort("contract abort"); } }
fn main() {
    for round in 32 {
        option = 41;
        let id = thread_spawn(snapshot);
        option = 99;
        qput(Gate { token: round });
        let result = qget<Result>();
        assert(result.value == 41);
        assert(result.bytes == "41");
        assert(thread_wait(id));
        assert(option == 99);
        for kind in 2 {
            let failed = kind == 1;
            let child = thread_spawn_contained(contained, failed);
            var message: u8[>..] = [];
            assert(thread_wait(child, message) == !failed);
            assert((message.len > 0) == failed);
            message.clear();
            assert(thread_wait(child, message) == !failed);
            assert(message.len == 0);
        }
    }
    print("thread synchronization contract ok");
}
