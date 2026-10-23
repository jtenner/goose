// Native-only cross-feature regression. Run test/conditional_shared_layout.py.
// Explicit DEBUG config required; this nested fixture has its own matrix.
import std;
import os;

struct Header {
    a: u32,
    const if build::DEBUG { debug: u64, } else {},
    c: u32,
}
// These are PRIVATE packed capability wrappers, never a serialized format.
// Capability representations are not the 4/8-byte aligned atomic cells.
struct Packed32 {
    prefix: u8,
    const if build::DEBUG { conditional_token32: SharedAtomicU32, } else {},
    tail: u8,
}
struct Packed64 {
    prefix: u8,
    const if build::DEBUG { conditional_token64: SharedAtomicU64, } else {},
    tail: u8,
}
fn header_size() -> u32 {
    const if build::DEBUG { return 16; } else { return 8; }
}
fn c_offset() -> u32 {
    const if build::DEBUG { return 12; } else { return 4; }
}
fn layout_id() -> u32 { return 0x48440000 + header_size(); }
fn names<T>() -> u8[>..] {
    var out: u8[>..] = [];
    const for <N, A> in fields<T> { format(out, N, ","); }
    return out;
}
fn make32(token: SharedAtomicU32) -> Packed32 {
    return Packed32 { prefix: 7,
        const if build::DEBUG { conditional_token32: token, } else {}, tail: 9 };
}
fn make64(token: SharedAtomicU64) -> Packed64 {
    return Packed64 { prefix: 11,
        const if build::DEBUG { conditional_token64: token, } else {}, tail: 13 };
}
fn bounce32(value: Packed32) -> Packed32 { let copied = value; return copied; }
fn bounce64(value: Packed64) -> Packed64 { let copied = value; return copied; }
fn private_capabilities(owner: SharedOwner) {
    // Native STORAGE remains aligned, irrespective of private wrapper layout.
    let token32 = shared_atomic_u32(owner, 104, 10);
    let token64 = shared_atomic_u64(owner, 112, 20);
    let x = bounce32(make32(token32));
    let y = bounce64(make64(token64));
    assert(x.prefix == 7 && x.tail == 9 && y.prefix == 11 && y.tail == 13);
    const if build::DEBUG {
        assert(names<Packed32>() == "prefix,conditional_token32,tail,");
        assert(names<Packed64>() == "prefix,conditional_token64,tail,");
        assert(atomic_fetch_add(x.conditional_token32, 2, "AcqRel") == 10);
        assert(atomic_fetch_add(y.conditional_token64, 3, "AcqRel") == 20);
        assert(atomic_load(token32, "Acquire") == 12);
        assert(atomic_load(token64, "Acquire") == 23);
    } else {
        assert(names<Packed32>() == "prefix,tail," && names<Packed64>() == "prefix,tail,");
        var private32: Packed32[1] = [x];
        var private64: Packed64[1] = [y];
        assert(bytes_of(private32).len == 2 && bytes_of(private64).len == 2);
    }
    return;
}
thread_fn misaligned_storage(width: i64) {
    let owner, ok = shared_alloc(64); assert(ok);
    if width == 32 { shared_atomic_u32(owner, 1, 0); }
    else { shared_atomic_u64(owner, 4, 0); }
}
fn inspect(a: SharedAccess) -> u32, bool {
    let size = shared_size(a);
    if size < 24 { return 0, false; }
    // Explicit application format. All metadata is validated before payload.
    if memory_read<u32>(a, 0, false) != 0x47434853 ||
       memory_read<u32>(a, 4, false) != 1 ||
       memory_read<u32>(a, 8, false) != layout_id() ||
       memory_read<u32>(a, 12, false) != header_size() ||
       memory_read<u32>(a, 16, false) != c_offset() ||
       memory_read<u32>(a, 20, false) != 0 || size != 24 + header_size() {
        return 0, false;
    }
    if memory_read<u32>(a, 24, false) != 7 { return 0, false; }
    const if build::DEBUG {
        if memory_read<u64>(a, 28, false) != 99 { return 0, false; }
    }
    return memory_read<u32>(a, 24 + c_offset(), false), true;
}
// Leading u8 intentionally misaligns the following CAPABILITY in the packed
// thread argument packet. The runtime/codegen must handle that representation.
thread_fn exchange(prefix: u8, input: SharedView, result: SharedView, flag: SharedAtomicU32) {
    assert(prefix == 3);
    let a = shared_borrow(input, 0, shared_size(input));
    let value, valid = inspect(a);
    shared_release(a);
    if valid {
        let out = shared_borrow(result, 0, 4);
        memory_write<u32>(out, 0, value + 1, false);
        shared_release(out);
    }
    atomic_store(flag, if valid { 1 } else { 2 }, "Release");
}
fn roundtrip(input: SharedView, result: SharedView, flag: SharedAtomicU32) -> u32, bool {
    assert(thread_wait(thread_spawn_contained(exchange, 3, input, result, flag)));
    let state = atomic_load(flag, "Acquire");
    assert(state == 1 || state == 2);
    if state == 2 { return 0, false; }
    let read = shared_borrow(result, 0, 4);
    let value = memory_read<u32>(read, 0, false);
    shared_release(read);
    return value, true;
}
fn report(value: u32, valid: bool) {
    if !valid { print("rejected layout"); exit(2); }
    assert(value == 287454021);
    print("accepted ", header_size(), " ", c_offset(), " ", value);
}
fn local(mode: u8[:], path: u8[:]) {
    var private: Header[1] = [Header { a: 7,
        const if build::DEBUG { debug: 99, } else {}, c: 287454020 }];
    assert(bytes_of(private).len == header_size());
    const if build::DEBUG { assert(names<Header>() == "a,debug,c,"); }
    else { assert(names<Header>() == "a,c,"); }
    let owner, ok = shared_alloc(128); assert(ok);
    private_capabilities(owner);
    for width in [32, 64] {
        var why: u8[>..] = [];
        assert(!thread_wait(thread_spawn_contained(misaligned_storage, width), why));
        assert(starts_with(why, "shared atomic alignment"));
    }
    let input = shared_view(owner, 0, 24 + header_size());
    let result = shared_view(owner, 64, 4); // disjoint result bytes, same owner
    let flag = shared_atomic_u32(owner, 96, 0);
    let write = shared_borrow(input);
    memory_write<u32>(write, 0, 0x47434853, false);
    memory_write<u32>(write, 4, 1, false);
    memory_write<u32>(write, 8, layout_id(), false);
    memory_write<u32>(write, 12, header_size(), false);
    memory_write<u32>(write, 16, c_offset(), false);
    memory_write<u32>(write, 20, 0, false);
    memory_write_bytes(write, 24, bytes_of(private)); // explicit private -> shared copy
    shared_release(write);
    if mode == "emit" {
        var image: u8[>..] = [];
        image.resize((24 + header_size()) as i64, 0);
        let read = shared_borrow(input);
        memory_read_bytes(read, 0, image);
        shared_release(read);
        assert(write_file(path, image));
        assert(shared_close(owner));
        return;
    }
    let value, valid = roundtrip(input, result, flag);
    // The worker changed shared result bytes; the live private original stays.
    assert(private[0].a == 7 && private[0].c == 287454020);
    const if build::DEBUG { assert(private[0].debug == 99); }
    assert(shared_close(owner)); // joined worker and released all borrows
    report(value, valid);
}
fn consume(path: u8[:], size: u64) {
    let mapped, mapped_ok = shared_map_readonly(path, size); assert(mapped_ok);
    let owner, ok = shared_alloc(128); assert(ok);
    let input = shared_view(mapped, 0, size);
    let result = shared_view(owner, 64, 4);
    let flag = shared_atomic_u32(owner, 96, 0);
    let value, valid = roundtrip(input, result, flag);
    assert(shared_close(owner) && shared_close(mapped));
    report(value, valid);
}
fn main() {
    let argv = args();
    if argv.len == 1 { local("normal", ""); return; }
    if argv.len == 3 && argv[1] == "emit" { local("emit", argv[2]); return; }
    if argv.len == 4 && argv[1] == "consume" {
        let size, ok = parse_int(argv[3]); assert(ok && size > 0);
        consume(argv[2], size as u64); return;
    }
    abort("conditional shared layout arguments");
}
