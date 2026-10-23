// runtime-debug: the ordinary string alias's image follows one byte.
let ORDER = "Release";
thread_fn worker(prefix: u8) { assert(prefix == 7 && ORDER == "Release"); }
fn main() {
    for repeat in 3 {
        assert(thread_wait(thread_spawn(worker, 7)));
        assert(thread_wait(thread_spawn_contained(worker, 7)));
    }
    print("worker packet alias passed");
}
