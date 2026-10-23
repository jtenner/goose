// error: cannot cross to C
extern fn take(v: SharedView);
fn main() { take(default<SharedView>()); }
