struct Mixed { a: i8, b: u8, c: i16, d: u16, e: i32, f: u32, g: i64, h: u64, bit: bool, x: f32, y: f64 }
struct Box<T> { lead: u8, item: T }
struct Padded { first: u8, pad, second: u32, pad 3, last: i16 }
struct Empty {}
struct Pads { pad 3 }
struct Nested { empty: Empty, pads: Pads, box: Box<i16>, mixed: Mixed, last: i64 }
fn main() {
    var m: Mixed = Mixed { a: -127, b: 250, c: -32000, d: 65000, e: -2000000000, f: 4000000000,
        g: -9223372036854775807, h: 18446744073709551615, bit: true, x: -0.0, y: 1.5 };
    print(m.a, ",", m.b, ",", m.c, ",", m.d, ",", m.e, ",", m.f);
    print(m.g, ",", m.h, ",", m.bit, ",", m.x, ",", m.y);
    var n: Nested = Nested { empty: Empty {}, pads: Pads {}, box: Box<i16> { lead: 9, item: -10 }, mixed: m, last: 77 };
    n.mixed.b += 10; n.box.item -= 2;
    assert(n.mixed.b == 4); assert(n.mixed.c == m.c); assert(n.mixed.d == m.d); assert(n.mixed.e == m.e);
    print("nested=", m.b, ",", n.mixed.b, ",", n.box.item, ",", n.last);
    var p: Padded = Padded { first: 1, second: 305419896, last: -3 };
    p.last += 2; print("pads=", p.first, ",", p.second, ",", p.last);
    var e1: Empty = Empty {}; var e2: Empty = copy(e1); assert(&e1 .!= &e2);
    var q: i16& = n.box.item; q += 4; print("address=", n.box.item);
}
