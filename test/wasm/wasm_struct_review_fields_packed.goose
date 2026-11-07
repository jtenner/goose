// warning: redundant &: o.leaf.g binds by reference here without it
// warning: redundant &: o.leaf.a binds by reference here without it
// warning: redundant &: o.leaf.bit binds by reference here without it
// warning: redundant &: o.leaf.x binds by reference here without it
// warning: redundant &: o.leaf.arr binds by reference here without it
struct Leaf { a: i8, b: u8, c: i16, d: u16, e: i32, f: u32, g: i64, h: u64, bit: bool, x: f32, y: f64, target: i64&, arr: i64[2] }
struct Outer { first: u8, leaf: Leaf, after: u16 }
recursive fn check(o: Outer&) {
    var a: i8 = &o.leaf.a; var b: u8 = &o.leaf.b;
    var c: i16 = &o.leaf.c; var d: u16 = &o.leaf.d;
    var e: i32 = &o.leaf.e; var f: u32 = &o.leaf.f;
    var g: i64 = &o.leaf.g; var h: u64 = &o.leaf.h;
    var bit: bool = &o.leaf.bit; var x: f32 = &o.leaf.x; var y: f64 = &o.leaf.y;
    var target: i64 = &o.leaf.target;
    assert(a == -9); assert(b == 250); assert(c == -30000); assert(d == 65000);
    assert(e == -2000000000); assert(f == 4000000000); assert(g == -8); assert(h == 18446744073709551615);
    assert(!bit); assert(x == 1.5); assert(y == -2.25); assert(target == 123);
    var address: i64& = &o.leaf.g; assert(address .== &o.leaf.g); address += 1; assert(o.leaf.g == -7);
    var small: i8& = &o.leaf.a; small += 1; assert(o.leaf.a == -8);
    var flag: bool& = &o.leaf.bit; flag = true; assert(o.leaf.bit);
    var number: f32& = &o.leaf.x; number += 0.5; assert(o.leaf.x == 2.0);
    var array: i64[2]& = &o.leaf.arr; var copied: i64[2] = copy(&o.leaf.arr);
    array[0] += 1; assert(o.leaf.arr[0] == 4); assert(copied[0] == 3); assert(copied[1] == 4);
    o.leaf.target += 1; assert(o.first == 5); assert(o.after == 60000);
}
fn main() {
    var backing: i64[] = [123];
    var o: Outer = Outer { first: 5, leaf: Leaf { a: -9, b: 250, c: -30000, d: 65000,
        e: -2000000000, f: 4000000000, g: -8, h: 18446744073709551615, bit: false,
        x: 1.5, y: -2.25, target: backing[0], arr: [3, 4] }, after: 60000 };
    var direct: i64 = &o.leaf.g; var false_bit: bool = &o.leaf.bit; var real: f64 = &o.leaf.y;
    assert(direct == -8); assert(!false_bit); assert(real == -2.25);
    check(o); print("fields=", o.leaf.g, ",", backing[0], ",", o.after);
}
