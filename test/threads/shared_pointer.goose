struct Pair { left: i64, right: i64 }

thread_fn publish(p: SharedPointer<Pair>) {
    let v = shared_pointer_copy(p);
    shared_pointer_store(p, Pair { left: v.left + 10, right: v.right + 20 });
}

thread_fn fail(p: SharedPointer<Pair>) { abort("contained pointer cleanup"); }
thread_fn read(p: SharedPointer<Pair>) { assert(shared_pointer_copy(p).left >= 1); }
thread_fn nested(p: SharedPointer<Pair>) {
    assert(thread_wait(thread_spawn(read, p)));
}
thread_fn put_arg(p: SharedPointer<Pair>) { assert(qput(p)); }
thread_fn retain_then_abort(p: SharedPointer<Pair>) {
    let extra = shared_pointer_retain(p);
    abort("retained claim cleanup");
}
thread_fn release_arg(p: SharedPointer<Pair>) { shared_pointer_release(p); }
thread_fn produce_owned() {
    let pointer, owner, ok = shared_pointer_alloc<Pair>(Pair { left: 51, right: 52 });
    assert(ok && qput(pointer));
}
thread_fn read_twice(a: SharedPointer<Pair>, b: SharedPointer<Pair>) {
    assert(shared_pointer_copy(a).left == shared_pointer_copy(b).left);
}

fn main() {
    let p, owner, ok = shared_pointer_alloc<Pair>(Pair { left: 1, right: 2 });
    assert(ok);
    assert(!shared_close(owner));
    let worker_p = shared_pointer_retain(p);
    assert(thread_wait(thread_spawn(publish, worker_p)));
    shared_pointer_release(worker_p);
    let v = shared_pointer_copy(p);
    print(v.left, " ", v.right);
    shared_pointer_release(p);
    assert(shared_close(owner));

    let queued, queue_owner, queue_ok = shared_pointer_alloc<Pair>(Pair { left: 7, right: 8 });
    assert(queue_ok && qput(queued));
    let received = qget<SharedPointer<Pair>>();
    print(shared_pointer_copy(received).left);
    shared_pointer_release(received);
    assert(shared_close(queue_owner));

    let kept, abort_owner, abort_ok = shared_pointer_alloc<Pair>(Pair { left: 3, right: 4 });
    assert(abort_ok);
    let doomed = shared_pointer_retain(kept);
    assert(!thread_wait(thread_spawn_contained(fail, doomed)));
    shared_pointer_release(doomed);
    shared_pointer_release(kept);
    assert(shared_close(abort_owner));

    let shared, shared_owner, shared_ok = shared_pointer_alloc<Pair>(Pair { left: 9, right: 10 });
    assert(shared_ok);
    var ids: i64[>..] = [];
    for i in 4 { ids.push(thread_spawn(read, shared)); }
    for i in 4 { assert(thread_wait(ids[i])); }
    assert(thread_wait(thread_spawn(nested, shared)));
    assert(thread_wait(thread_spawn(read_twice, shared, shared)));
    assert(thread_wait(thread_spawn(put_arg, shared)));
    let from_worker = qget<SharedPointer<Pair>>();
    assert(shared_pointer_copy(from_worker).left == 9);
    shared_pointer_release(from_worker);
    assert(!thread_wait(thread_spawn_contained(retain_then_abort, shared)));
    assert(shared_pointer_copy(shared).right == 10);
    shared_pointer_release(shared);
    assert(shared_close(shared_owner));

    let existing, existing_ok = shared_alloc(64);
    assert(existing_ok);
    let in_owner, in_ok = shared_pointer_alloc<Pair>(existing, 16,
        Pair { left: 31, right: 32 });
    assert(in_ok && shared_pointer_copy(in_owner).right == 32);
    shared_pointer_release(in_owner);
    let access = shared_borrow(shared_view(existing, 16, 16));
    shared_release(access);
    assert(shared_close(existing));

    let released, released_owner, released_ok =
        shared_pointer_alloc<Pair>(Pair { left: 41, right: 42 });
    assert(released_ok);
    assert(thread_wait(thread_spawn_contained(release_arg,
        shared_pointer_retain(released))));
    shared_pointer_release(released);
    assert(shared_close(released_owner));

    assert(thread_wait(thread_spawn(produce_owned)));
    let produced = qget<SharedPointer<Pair>>();
    assert(shared_pointer_copy(produced).right == 52);
    shared_pointer_release(produced);
}
