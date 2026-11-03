// error: cannot pass between threads: it holds an index type
var items: i64[>..] = [];
fn main() { channel<u32 in items>(); }
