thread_fn produce() -> u8[9000000] { [7; 9000000] }
thread_fn fail() -> u8[9000000] { assert(false); [9; 9000000] }
fn main() {
    let value, ok = thread_join(thread_spawn_join(produce));
    assert(ok && value[0] == 7 && value[8999999] == 7);
    let empty, failed = thread_join(thread_spawn_contained_join(fail));
    assert(!failed && empty[0] == 0 && empty[8999999] == 0);
    print(value[8999999]);
}
