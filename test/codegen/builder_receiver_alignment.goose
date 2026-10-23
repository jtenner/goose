// runtime-debug: capture the original packed header and stack before the RHS
// can rebind the receiver. The first global count is deliberately at offset 9.
var marker: u8 = 1;
var bytes: u8[>..] = [];
var other: u8[>..] = [];
enum Choice { One, Two }
fn invoke<F>() -> u8[>..] { return F(); }

fn direct() {
    var dst: u8[>..]& = bytes;
    fn rhs() -> u8[>..] { dst .= other; return "abc"; }
    dst = rhs();
    assert(bytes == "abc" && other.len == 0 && dst.len == 0);
}
fn dispatch(c: Choice) {
    var dst: u8[>..]& = bytes;
    fn rhs(c: Choice.One) -> u8[>..] { dst .= other; return "def"; }
    fn rhs(c: Choice.Two) -> u8[>..] { dst .= other; return "ghij"; }
    dst = rhs(c);
    match c {
        One => assert(bytes == "def"),
        Two => assert(bytes == "ghij"),
    }
    assert(other.len == 0 && dst.len == 0);
}
fn function_value() {
    var dst: u8[>..]& = bytes;
    dst = invoke() { dst .= other; "klm" };
    assert(bytes == "klm" && other.len == 0 && dst.len == 0);
}
fn block_value(c: bool) {
    var dst: u8[>..]& = bytes;
    dst = { dst .= other; if c { "nop" } else { "qrst" } };
    if c { assert(bytes == "nop"); } else { assert(bytes == "qrst"); }
    assert(other.len == 0 && dst.len == 0);
}
fn element_run() {
    var dst: u8[>..]& = bytes;
    fn rhs() -> u8[u8] { dst .= other; return "uvw"; }
    dst = rhs();
    assert(bytes == "uvw" && other.len == 0 && dst.len == 0);
}
fn fallback() {
    var dst: u8[>..]& = bytes;
    fn leave() { dst .= other; return "xyz" from rhs; }
    fn rhs() -> u8[u8] { leave(); return "unused"; }
    dst = rhs();
    assert(bytes == "xyz" && other.len == 0 && dst.len == 0);
}

// Normal copyback must not run when dispatch leaves the assignment's function.
fn nonlocal(c: Choice) -> u8[>..] {
    var dst: u8[>..]& = bytes;
    fn rhs(c: Choice.One) -> u8[>..] {
        dst .= other;
        return "caught" from nonlocal;
    }
    fn rhs(c: Choice.Two) -> u8[>..] { dst .= other; return "normal"; }
    dst = rhs(c);
    assert(bytes == "normal" && other.len == 0 && dst.len == 0);
    return "done";
}

struct Frame { tag: u8, items: u8[>..] }
struct Record { prefix: u8[u8], items: u8[>..] }
var frame_a = Frame { tag: 2, items: "old" };
var frame_b = Frame { tag: 3, items: "other" };
var record_a = Record { prefix: "a", items: "old" };
var record_b = Record { prefix: "b", items: "other" };
fn tails() {
    var fdst: Frame& = frame_a;
    fn frame_rhs() -> u8[>..] { fdst .= frame_b; return "frame"; }
    fdst.items = frame_rhs();
    assert(frame_a.tag == 2 && frame_a.items == "frame" && frame_b.items == "other");
    // The tail's data address differs from its count's owning header base.
    var rdst: Record& = record_a;
    fn record_rhs() -> u8[>..] { rdst .= record_b; return "record"; }
    rdst.items = record_rhs();
    assert(record_a.prefix == "a" && record_a.items == "record");
    assert(record_b.prefix == "b" && record_b.items == "other");
}
fn main() {
    direct();
    function_value();
    block_value(true);
    block_value(false);
    element_run();
    fallback();
    for i in 2 {
        let choice: Choice = if i == 0 { Choice.One {} } else { Choice.Two {} };
        dispatch(choice);
        bytes.clear();
        let result = nonlocal(choice);
        if i == 0 { assert(result == "caught" && bytes.len == 0); }
        else { assert(result == "done" && bytes == "normal"); }
        assert(other.len == 0);
    }
    tails();
    assert(marker == 1);
    print("builder receiver alignment passed");
}
