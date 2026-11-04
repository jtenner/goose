// error: SharedPointer value type must be recursively fixed and flat
var ITEMS: i64[>..] = [1, 2];
type Item = u8 in ITEMS;
fn main() { qpoll<SharedPointer<Item>>(); }
