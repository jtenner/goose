struct Aligned { align(64) value: u32 }
struct Wrapper<T> { value: T }
// error: Thread payload cannot contain aligned values
fn use(handle: Thread<Wrapper<Aligned>>) {}
fn main() {}
