var order = 0;

fn fixed(expected: i64, seed: u8) -> u8[3] {
    assert(order == expected);
    order++;
    [seed, seed + 1, seed + 2]
}

fn owner_arg(expected: i64, owner: SharedOwner) -> SharedOwner {
    assert(order == expected);
    order++;
    owner
}

fn offset_arg(expected: i64) -> i64 {
    assert(order == expected);
    order++;
    16
}

fn pointer_arg(expected: i64, pointer: SharedPointer<u8[..8]>) -> SharedPointer<u8[..8]> {
    assert(order == expected);
    order++;
    pointer
}

fn check(value: u8[..8], seed: u8) {
    assert(value.len == 3);
    assert(value[0] == seed);
    assert(value[1] == seed + 1);
    assert(value[2] == seed + 2);
}

fn main() {
    let pointer, owner, ok = shared_pointer_alloc<u8[..8]>(fixed(0, 7));
    assert(ok);
    check(shared_pointer_copy(pointer), 7);

    let storage, storage_ok = shared_alloc(64);
    assert(storage_ok);
    let placed, placed_ok = shared_pointer_alloc<u8[..8]>(
        owner_arg(1, storage), offset_arg(2), fixed(3, 17));
    assert(placed_ok);
    check(shared_pointer_copy(placed), 17);

    shared_pointer_store(pointer_arg(4, pointer), fixed(5, 27));
    check(shared_pointer_copy(pointer), 27);
    assert(order == 6);

    shared_pointer_release(placed);
    assert(shared_close(storage));
    shared_pointer_release(pointer);
    assert(shared_close(owner));
    print("converted");
}
