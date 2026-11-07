struct Item { value: i64&, marker: u8 }
struct Inner { before: u16, fixed: Item&[2], limited: Item&[..3], after: u16 }
struct Outer { before: u8, inner: Inner, after: u16 }
var first: i64[] = [10]; var second: i64[] = [20];
var a: Item = Item { value: first[0], marker: 1 }; var b: Item = Item { value: second[0], marker: 2 };
var global: Outer = Outer { before: 7, inner: Inner { before: 60000, fixed: [a, b], limited: [a, b], after: 65000 }, after: 50000 };
fn main() {
    var local: Outer = copy(global); local.inner.fixed[0].value += 1;
    assert(first[0] == 11); local.inner.fixed[0] .= b;
    assert(local.inner.fixed[0] .== &b); assert(global.inner.fixed[0] .== &a);
    assert(local.inner.fixed[0].marker == 2); assert(global.inner.fixed[0].marker == 1);
    var pushed: Item& = local.inner.limited.push(a); assert(pushed .== &a);
    var popped: Item& = local.inner.limited.pop(); assert(popped .== &a);
    local.inner.limited.clear(); local.inner.limited.push(b); local.inner.limited.pop();
    local.inner.limited.push(a); local.inner.limited[0].value += 2;
    assert(first[0] == 13); assert(second[0] == 20); assert(global.inner.limited.len == 2);
    assert(local.before == 7); assert(local.inner.before == 60000); assert(local.inner.after == 65000); assert(local.after == 50000);
    print("references=", first[0], ",", second[0], ",", global.inner.limited.len, ",", local.inner.limited.len);
}
