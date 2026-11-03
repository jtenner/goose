// error: cannot cross thread contexts: its payload holds an index type
var items: i64[>..] = [];
fn use(handle: Thread<u32 in items>) {}
fn main() {}
