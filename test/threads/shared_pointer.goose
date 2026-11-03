struct Pair { left: i64, right: i64 }

thread_fn publish(p: SharedPointer<Pair>) {
    let v = shared_pointer_copy(p);
    shared_pointer_store(p, Pair { left: v.left + 10, right: v.right + 20 });
}

thread_fn fail(p: SharedPointer<Pair>) { abort("contained pointer cleanup"); }

fn main() {
    let p, owner, ok = shared_pointer_alloc<Pair>(Pair { left: 1, right: 2 });
    assert(ok);
    assert(!shared_close(owner));
    let worker_p = shared_pointer_retain(p);
    assert(thread_wait(thread_spawn(publish, worker_p)));
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
    shared_pointer_release(kept);
    assert(shared_close(abort_owner));
}
