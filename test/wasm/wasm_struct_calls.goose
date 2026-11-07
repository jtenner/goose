struct Item { tag: u8, value: i64, next: Item? }
var original: Item = Item { tag: 1, value: 5 };
var duplicate: Item = copy(original);
recursive fn pick(a: Item&) -> Item& { return a; }
inline fn inline_pick(a: Item&) -> Item& { return a; }
fn apply<F>(n: i64) -> i64 { F(n) }
recursive fn visit(n: i64, parent: Item&) -> i64 {
    var local: Item = Item { tag: 2, value: n };
    defer { print("defer=", local.value); }
    if n > 0 { return visit(n - 1, local) + parent.value; }
    return local.value + parent.value;
}
fn main() {
    var a: Item = Item { tag: 3, value: 10, next: original };
    var b: Item = copy(pick(a)); var c: Item = copy(inline_pick(a));
    var d: Item = copy(a);
    print("mapped=", apply(3) { x => original.value + x });
    b.value += 1; c.value += 2; d.value += 3;
    print("copies=", a.value, ",", b.value, ",", c.value, ",", d.value);
    var next: Item? = a.next; if next != null { print("next=", next.value, ",", b.next .== next); }
    duplicate.value = 99; print("globals=", original.value, ",", duplicate.value);
    var optional: Item? = null; print(optional == null); optional .= a;
    if optional != null { print("optional=", optional.value); }
    print("visit=", visit(3, a));
}
