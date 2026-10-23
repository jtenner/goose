// error: cannot cross to C
struct Cap { v: SharedView }
extern fn take(v: Cap);
fn main() {}
