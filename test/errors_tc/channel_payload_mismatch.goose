// error: expected a value of type i64, got bool
fn main() {
    let ch = channel<i64>();
    channel_send(ch, true);
}
