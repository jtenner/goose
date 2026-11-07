var global: u8[..] = "hi";
fn change(a: u8[..]&) -> i64 { a[0] = 88; return a.cap; }
fn main() {
    var a: u8[..] = [..8]; a.push(97); a.push(98); a.push(99);
    print("capture=", a, "|", change(a), "|", a);
    var literal: u8[..] = "a\0b"; print(literal.cap, ",", literal.len, ",", literal);
    var filled: u8[..] = [65; 2]; print("fill=", filled, ",", filled.cap);
    var optional: u8[..]? = null; print(optional); optional .= a; print(optional);
    a.clear(); a.push(80); a.push(81); print("clear=", a.cap, ",", a.len, ",", a);
    a.pop(); a.push(82); print("regrow=", a);
    var n = 70000; var large: u8[..] = [..n];
    for i in n { large.push(120); }
    { let stable = &large[0]; print("stable=", stable); }
    large.clear(); large.push(121); print("large=", large.cap, ",", large.len, ",", large[0]);
    print("global=", global, ",", global.cap);
}
