// A later payload expression may rebind the earlier channel operand.
struct ScalarBox { ch: Channel<i64> }
fn redirect(box: ScalarBox&, replacement: Channel<i64>) -> i64 {
    box.ch = replacement;
    7
}

struct BytesBox { ch: Channel<u8[>..]> }
fn redirect_bytes(box: BytesBox&, replacement: Channel<u8[>..]>) -> u8[>..] {
    box.ch = replacement;
    var bytes: u8[>..] = [3, 4, 5];
    bytes
}

fn main() {
    let first = channel<i64>();
    let replacement = channel<i64>();
    var scalar = ScalarBox { first };
    assert(channel_send(scalar.ch, redirect(scalar, replacement)));
    let value, got = channel_try_receive(first);
    let other, other_got = channel_try_receive(replacement);
    assert(got && value == 7 && !other_got);

    let bytes_first = channel<u8[>..]>();
    let bytes_replacement = channel<u8[>..]>();
    var bytes = BytesBox { bytes_first };
    assert(channel_try_send(bytes.ch, redirect_bytes(bytes, bytes_replacement)));
    let packet, packet_got = channel_try_receive(bytes_first);
    let other_packet, other_packet_got = channel_try_receive(bytes_replacement);
    assert(packet_got && packet.len == 3 && packet[1] == 4 && !other_packet_got);
    print("ordered");
}
