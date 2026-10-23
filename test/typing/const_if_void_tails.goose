// dump-runtime: void tails are determined after entering selected lexical scopes.
fn inferred(b: bool) { const if true { if b { print("inferred"); } } }
fn known_void(b: bool) { if b { return; } const if true { if b { print("known"); } } }
fn disabled(b: bool) { const if false { if b { missing(); } } }
fn nested(b: bool) {
    const if true { if b { const if true { if b { print("nested"); } } } else {} }
}
fn expanded(b: bool) {
    const for <C> in [true, false] { const if C { if b { print("expanded"); } } }
}
fn main() {
    inferred(true); known_void(false); disabled(true); nested(true); expanded(true);
}
