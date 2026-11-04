fn fixed() -> u8[3] { [7, 8, 9] }
struct Frame { tag: u8, tail: u8[>..] }
struct Packed { prefix: u8[], tail: u8[>..] }
fn main() {
    let x: u8[3] = [7, 8, 9];
    let y: u8[..8] = [7, 8, 9];
    let ch = channel<u8[>..]>(8);
    assert(channel_send(ch, x));
    assert(channel_try_send(ch, x));
    assert(channel_send(ch, y));
    assert(channel_try_send(ch, y));
    assert(channel_send(ch, fixed()));
    assert(channel_try_send(ch, fixed()));
    assert(channel_send(ch, [7, 8, 9]));
    assert(channel_try_send(ch, [7, 8, 9]));
    for i in 0..8 {
        let value, ok = channel_receive(ch);
        assert(ok && value.len == 3 && value[0] == 7 && value[2] == 9);
    }
    let bytes = channel<u8[]>();
    assert(channel_send(bytes, x));
    assert(channel_try_send(bytes, y));
    assert(channel_send(bytes, fixed()));
    assert(channel_try_send(bytes, fixed()));
    for i in 0..4 {
        let value, ok = channel_receive(bytes);
        assert(ok && value.len == 3 && value[0] == 7 && value[2] == 9);
    }
    let limited = channel<u8[..8]>();
    assert(channel_send(limited, x));
    assert(channel_try_send(limited, y));
    assert(channel_send(limited, fixed()));
    assert(channel_try_send(limited, fixed()));
    for i in 0..4 {
        let value, ok = channel_receive(limited);
        assert(ok && value.len == 3 && value[0] == 7 && value[2] == 9);
    }
    let frames = channel<Frame>();
    let frame = Frame { 4, [7, 8, 9] };
    assert(channel_send(frames, copy(frame)));
    assert(channel_try_send(frames, Frame { 4, [7, 8, 9] }));
    for i in 0..2 {
        let value, ok = channel_receive(frames);
        assert(ok && value.tag == 4 && value.tail.len == 3 && value.tail[2] == 9);
    }
    let packed = channel<Packed>();
    assert(channel_send(packed, Packed { [1, 2], [7, 8, 9] }));
    assert(channel_try_send(packed, Packed { [1, 2], [7, 8, 9] }));
    for i in 0..2 {
        let value, ok = channel_receive(packed);
        assert(ok && value.prefix.len == 2 && value.prefix[1] == 2);
        assert(value.tail.len == 3 && value.tail[2] == 9);
    }
    print("converted");
}
