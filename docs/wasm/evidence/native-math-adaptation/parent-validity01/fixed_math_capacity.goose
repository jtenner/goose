// runtime-debug: the source result must fit before the receiver changes.
fn main() {
    var source: i64[2] = [7, -8];
    var receiver: i64[..] = [..1];
    receiver.push(42);
    print(receiver.len, " ", receiver[0]);
    receiver = -source;
    print("not reached");
}
