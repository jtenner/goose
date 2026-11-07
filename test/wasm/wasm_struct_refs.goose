struct Item { marker: u8, value: i64 }
struct Mixed { before: u8, target: i64&, after: u16, data: i64[]? }
fn main() {
    var a: Item = Item { marker: 1, value: 10 }; var b: Item = Item { marker: 2, value: 20 };
    var f: Item&[2] = [a, b]; var l: Item&[..3] = [a]; l.push(b);
    var v: Item&[] = [a, b]; var u: Item&[varint] = [a, b];
    var r: Item&[..] = [..3]; r.push(a); r.push(b);
    var g: Item&[>..] = [a]; g.push(b);
    f[0].value += 1; l[1].value += 2; v[0].value += 3; u[1].value += 4;
    r[0].value += 5; g[1].value += 6;
    for &x in g { x.value += 10; }
    var copied: Item&[] = copy(v); assert(copied == v);
    copied[0] .= b; print("refs=", a.value, ",", b.value, ",", v[0].value, ",", copied[0].value);
    var x: i64[] = [100]; var y: i64[] = [200];
    var m: Mixed = Mixed { before: 3, target: x[0], after: 60000, data: y };
    var data: i64[]? = m.data; if data != null { print("data=", m.target, ",", data.len, ",", data[0]); }
    m.target .= y[0]; m.target += 7;
    var n: Mixed = copy(m); n.target += 8;
    print("identity=", x[0], ",", y[0], ",", n.target .== m.target, ",", m.before, ",", m.after);
    l.clear(); var pushed: Item& = l.push(a); assert(pushed .== a);
    var popped: Item = copy(l.pop()); popped.value += 1;
    l.push(b); l.pop(); print("returned=", a.value, ",", popped.value, ",", l.len);
}
