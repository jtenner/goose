// error: channel_wait_any channels must have the same payload type
fn main() {
    let a = channel<i64>();
    let b = channel<bool>();
    channel_wait_any(a, b);
}
