// runtime-debug: zero-byte arguments and overflow rejection during packet construction.
enum Empty { Zero }
var bytes: u8[>..] = [];
thread_fn worker(prefix: u8, none: u8[0], zero: Empty.Zero, var local: u8[>..]) {
    assert(prefix == 7 && none.len == 0 && local.len == bytes.len);
    for b, i in local { assert(b == bytes[i] && b == 17); }
    let n = local.len;
    local.push(44); bytes.push(55);
    assert(local.len == n + 1 && bytes.len == n + 1);
    assert(local[n] == 44 && bytes[n] == 55);
}
fn make(n: u64) -> u8[>..] {
    var result: u8[>..] = [];
    result.resize(n, 0);
    return result;
}
thread_fn consume(prefix: u8, var data: u8[>..]) { abort("unexpected payload worker"); }
thread_fn invalid(prefix: u8, n: u64) { thread_spawn(consume, prefix, make(n)); }
fn main() {
    for n in 0..4 {
        assert(bytes.len == n);
        assert(thread_wait(thread_spawn(worker, 7, [], Empty.Zero {}, copy(bytes))));
        assert(thread_wait(thread_spawn_contained(worker, 7, [], Empty.Zero {}, copy(bytes))));
        assert(bytes.len == n);
        var why: u8[>..] = [];
        assert(!thread_wait(thread_spawn_contained(invalid, 7, 9223372036854775808), why));
        let expected = "resize to a negative length";
        assert(why.len >= expected.len);
        for ch, i in expected { assert(why[i] == ch); }
        bytes.push(17);
    }
    print("worker packet counts passed");
}
