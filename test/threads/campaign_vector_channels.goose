import simd_vectors;
thread_fn publish(p: SharedPointer<u32x4>, ch: Channel<u32x4>) -> u32x4 {
    let value = shared_pointer_copy(p) + splat_u32x4(1);
    assert(channel_send(ch, value));
    shuffle_u32x4(value, 3, 2, 1, 0)
}
fn main() {
    let input: u32x4 = [1, 2, 3, 4];
    let owner, allocated = shared_alloc(16);
    assert(allocated);
    let pointer, placed = shared_pointer_alloc<u32x4>(owner, 0, input);
    assert(placed);
    let ch = channel<u32x4>(1);
    let handle = thread_spawn_contained_join(publish, pointer, ch);
    let result, joined = thread_join(handle);
    let message, received = channel_receive(ch);
    assert(joined && received);
    assert(result[0] == 5 && result[3] == 2);
    assert(message[0] == 2 && message[3] == 5);
    assert(shared_pointer_copy(pointer)[0] == 1);
    shared_pointer_release(pointer);
    assert(shared_close(owner));
    print(result[0], " ", message[3]);
}
