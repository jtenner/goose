// runtime-debug: UTF-8 continuation checks and recovery after malformed bytes.
import std;

fn check(bytes: u8[:], expected: i64[:]) {
    var actual: i64[>..] = [];
    each_utf8(bytes) { actual.push(it); };
    assert(actual == expected);
}

fn main() {
    // F7: an ASCII byte after a lead byte must remain a separate code point.
    check([0xC2, 0x41], [65533, 65]);
    check([0xE2, 0x41, 0xAC], [65533, 65, 65533]);
    check([0xE2, 0x82, 0x41], [65533, 65533, 65]);
    check([0xF0, 0x41, 0x98, 0x80], [65533, 65, 65533, 65533]);
    check([0xF0, 0x9F, 0x41, 0x80], [65533, 65533, 65, 65533]);
    check([0xF0, 0x9F, 0x98, 0x41], [65533, 65533, 65533, 65]);

    // Bytes above the continuation range must also be rejected.
    check([0xC2, 0xFF], [65533, 65533]);
    check([0xE2, 0xFF, 0xAC], [65533, 65533, 65533]);
    check([0xE2, 0x82, 0xFF], [65533, 65533, 65533]);
    check([0xF0, 0xFF, 0x98, 0x80], [65533, 65533, 65533, 65533]);
    check([0xF0, 0x9F, 0xFF, 0x80], [65533, 65533, 65533, 65533]);
    check([0xF0, 0x9F, 0x98, 0xFF], [65533, 65533, 65533, 65533]);
    check([0xC2, 0xC2, 0xA2], [65533, 162]);
    check([0xE2, 0xC2, 0xA2], [65533, 162]);
    check([0xF0, 0xE2, 0x82, 0xAC], [65533, 8364]);

    // Empty, ASCII and valid two-, three- and four-byte sequences.
    check("", []);
    check([0, 65, 127], [0, 65, 127]);
    check([0xC2, 0x80, 0xDF, 0xBF], [128, 2047]);
    check([0xE0, 0xA0, 0x80, 0xEF, 0xBF, 0xBF], [2048, 65535]);
    check([0xF0, 0x90, 0x80, 0x80, 0xF4, 0x8F, 0xBF, 0xBF], [65536, 1114111]);
    check("A¢€😀Z", [65, 162, 8364, 128512, 90]);

    // Stray continuation bytes and incomplete sequences consume one byte.
    check([0x80, 0xBF], [65533, 65533]);
    check([0xC2], [65533]);
    check([0xE2], [65533]);
    check([0xE2, 0x82], [65533, 65533]);
    check([0xF0], [65533]);
    check([0xF0, 0x9F], [65533, 65533]);
    check([0xF0, 0x9F, 0x98], [65533, 65533, 65533]);
    let full: u8[4] = [0xF0, 0x9F, 0x98, 0x80];
    check(full[..1], [65533]);
    check(full[..2], [65533, 65533]);
    check(full[..3], [65533, 65533, 65533]);
    print("utf8 ok");
}
