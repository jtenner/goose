---
name: goose-language
description: Write idiomatic Goose programs, including safe concurrency and shared memory.
---

# Goose language

Use `docs/reference.md` for language details and `docs/goose_spec.md` for the
normative rules. Use `let` for values that do not change, `var` for mutable
storage, explicit types where they clarify an interface, and check boolean
results before using returned values. Prefer slices for reading sequences and
value types for data that must cross worker boundaries. Functions can return
several values; a final expression supplies the result.

```goose
fn sum(xs: i64[:]) -> i64 {
    var total: i64 = 0;
    for x in xs { total += x; }
    total
}

fn main() {
    let values: i64[3] = [1, 2, 3];
    print(sum(values));
}
```

## Safe threading

Declare workers with `thread_fn`. Ordinary references and mutable globals do
not share state across workers; send flat values or explicitly supported
capabilities. Prefer structured spawn and join: the handle belongs to the
spawning instance, cannot be sent onward, and is consumed exactly once. A child
cannot outlive its spawner; cleanup cancels contained descendants before it
joins unjoined children. Check the join boolean, especially for contained
workers whose abort is reported there.

Each `channel<T>()` is a separate FIFO. Handle copies name the same channel,
and worker handoff retains it. Agree which producer closes it; close once when
no more sends are needed. Receivers can drain committed messages after close;
check the boolean to distinguish a value from closed or cancelled. A bounded
channel needs a positive capacity and may block a sender. Try operations do not
wait. Cancellation is cooperative: a contained worker should check
`thread_cancelled()` and return; blocked channel operations wake and fail on
cancellation. Always join even after requesting cancellation.

`channel_wait_any` chooses the lowest ready argument index, including a closed
channel; `-1` means cancellation. It does not reserve a message, so check the
subsequent receive, especially with competing consumers.

```goose
thread_fn produce(ch: Channel<i64>) -> i64 {
    if thread_cancelled() { return 0; }
    if channel_send(ch, 42) { 1 } else { 0 }
}

fn main() {
    let ch = channel<i64>(1);
    let worker = thread_spawn_contained_join(produce, ch);
    let n, ok = thread_join(worker);
    assert(ok && n == 1);
    assert(channel_close(ch));
    let index = channel_wait_any(ch);
    assert(index == 0);
    let value, received = channel_receive(ch);
    assert(received && value == 42);
}
```

## Safe SharedPointer use

Use `SharedPointer<T>` only for fixed-size, recursively flat values: no
references, slices, strings, runtime-sized arrays, capabilities, function
values or variable-mode ADTs anywhere inside `T`. Allocation copies in;
`shared_pointer_copy` copies out and `shared_pointer_store` copies in. No
reference to the stored object escapes. Individual operations are synchronized;
a copy followed by a store is not one atomic update.

Assignment makes an alias of the same claim, not a retain. Release invalidates
that claim and all its aliases. Retain explicitly for an independent claim and
release each claim once, then close the owner. A direct stored pointer passed
to a worker gives it a distinct claim while preserving the source; a temporary
claim is consumed. A successful `qput` of exactly `SharedPointer<T>` transfers
its claim and invalidates sender aliases; a failed put leaves it owned by the
sender. Do not wrap it to bypass worker or queue restrictions. For an existing
owner, reserve a nonoverlapping range: pointer objects cannot overlap ordinary
borrows, atomic regions, or other live pointer objects.

```goose
struct Pair { left: i64, right: i64 }

fn main() {
    let p, owner, ok = shared_pointer_alloc<Pair>(Pair { left: 1, right: 2 });
    assert(ok);
    let independent = shared_pointer_retain(p);
    let value = shared_pointer_copy(independent);
    shared_pointer_store(p, Pair { left: value.left + 1, right: value.right });
    shared_pointer_release(independent);
    shared_pointer_release(p);
    assert(shared_close(owner));
}
```

## Atomics

Use typed `SharedAtomicU32` or `SharedAtomicU64` cells registered on a shared
owner, or derive a cell from a typed atomic array view. Keep their bytes out of
ordinary borrows and other registrations. Use `atomic_load`, `atomic_store`,
`atomic_exchange`, `atomic_fetch_add/sub/and/or/xor`, and strong
`atomic_compare_exchange`; fetch and exchange return the old value, and CAS
returns the observed value and success. Arithmetic wraps at the cell width.

Orders are compile-time strings. Loads allow `"Relaxed"`, `"Acquire"`,
`"SeqCst"`; stores allow `"Relaxed"`, `"Release"`, `"SeqCst"`; read-modify-write
operations allow all five, including `"AcqRel"`. CAS failure can be `"Relaxed"`
with any success order, `"Acquire"` with Acquire, AcqRel or SeqCst success, or
`"SeqCst"` only with SeqCst success. Choose acquire/release to publish data,
relaxed for independent counters, and SeqCst when a single global order is
needed. Raw-address `unsafe_atomic_*` operations are forbidden in safe Goose;
do not try to extract addresses from capabilities. See spec §11.4 for target
and lifetime requirements.
