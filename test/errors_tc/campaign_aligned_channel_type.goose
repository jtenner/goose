struct Aligned { align(64) value: u32 }
struct Wrapper<T> { value: T }
// error: Channel payload cannot contain aligned values
fn use(ch: Channel<Wrapper<Aligned>>) {}
fn main() {}
