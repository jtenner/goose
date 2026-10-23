// runtime-debug: packed builder headers must not escape as int64_t* result channels.
// The first builder's length is at offset 9 in the generated globals, after
// a byte and its packed base pointer. This fails deterministically under
// -fsanitize=alignment, independently of local C stack placement.
var marker: u8 = 7;
fn make(n: i64) -> u8[>..] {
    var out: u8[>..] = [];
    for i in n { out.push((65 + i) as u8); }
    return out;
}
var direct: u8[>..] = make(3);

enum Choice { One, Two }
fn choose(c: Choice.One) -> u8[>..] { return make(1); }
fn choose(c: Choice.Two) -> u8[>..] { return make(2); }
fn dispatched(c: Choice) -> u8[>..] { return choose(c); }
var selected: u8[>..] = dispatched(Choice.Two {});

// An element-run twin returns a variable array into a builder's header.
fn array(n: i64) -> u8[u8] {
    var out: u8[>..] = [];
    for i in n { out.push((97 + i) as u8); }
    return out;
}
var run: u8[>..] = array(3);

struct Frame { tag: u8, items: u8[>..] = make(2) }
struct Record { prefix: u8[u8], items: u8[>..] }
fn frame() -> Frame { return Frame { tag: 9, items: make(2) }; }
fn record() -> Record { return Record { prefix: "x", items: make(3) }; }
fn pair(n: i64) -> u8[>..], u8[>..], Frame {
    return make(n), make(n + 1), frame();
}
fn forward(n: i64) -> u8[>..], u8[>..], Frame { return pair(n); }
fn pair(c: Choice.One) -> u8[>..], u8[>..], Frame { return pair(1); }
fn pair(c: Choice.Two) -> u8[>..], u8[>..], Frame { return pair(2); }
fn forward(c: Choice) -> u8[>..], u8[>..], Frame { return pair(c); }

// A result channel is also a construction lvalue, including branches and
// nested calls; a nonlocal exit must skip normal result copyback.
fn branch(c: bool) -> u8[>..] {
    return if c { make(2) } else { make(3) };
}
recursive fn leave(n: i64) {
    if n > 0 { leave(n - 1); }
    return forward(2) from caught;
}
fn caught() -> u8[>..], u8[>..], Frame {
    leave(1);
    return pair(0);
}
fn early() -> Frame {
    return Frame { tag: 0, items: { leave_early(); make(0) } };
}
fn leave_early() { return frame() from early; }

var order: u8 = 0;
fn next(n: u8) -> i64 { order = order * 10 + n; return n; }
fn args(a: i64, b: u8[>..], c: i64) -> u8[>..] {
    assert(a == 1 && b == "AB" && c == 3);
    return b;
}
fn main() {
    assert(marker == 7 && direct == "ABC" && selected == "AB" && run == "abc");
    let a, b, f = forward(2);
    assert(a == "AB" && b == "ABC" && f.tag == 9 && f.items == "AB");
    let c, d, g = forward(Choice.One {});
    assert(c == "A" && d == "AB" && g.items == "AB");
    let h, i, j = caught();
    assert(h == "AB" && i == "ABC" && j.items == "AB");
    assert(branch(true) == "AB" && branch(false) == "ABC");
    var nested = Frame { tag: 8, items: args(next(1), make(next(2)), next(3)) };
    assert(order == 123 && nested.tag == 8 && nested.items == "AB");
    nested.items.push('!');
    assert(nested.items == "AB!");
    let defaults = Frame { tag: 4, .. };
    assert(defaults.items == "AB");
    let r = record();
    assert(r.prefix == "x" && r.items == "ABC");
    assert(early().items == "AB");
    make(1);
    array(1);
    pair(Choice.Two {});
    print("builder return alignment passed");
}
