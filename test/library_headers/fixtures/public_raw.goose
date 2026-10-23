export fn pointer(v: UnsafePtr) -> UnsafePtr { v }
export fn pointer_ref(v: const UnsafePtr&) -> UnsafePtr { v }
export fn pointer_slice(v: const UnsafePtr[:]) -> UnsafePtr { v[0] }
