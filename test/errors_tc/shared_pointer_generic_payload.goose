// error: SharedPointer value type must be recursively fixed and flat
fn poll<T>() { qpoll<SharedPointer<T>>(); }
fn main() { poll<u8[:]>(); }
