var global_fixed: i16[3] = [-32768, 2, -1];
var global_limited: u8[..65536] = [];
var marker: i64 = 123;
fn mutate(a: i16[3]&) { a[1] += 5; for &v in a { v += 1; } }
fn append(a: u8[..4]&, n: u8) { a.push(n); }
fn empty(a: const u8[0]&) { print("empty=", a.len); }
fn main() {
    var fixed: i16[3] = [1, 2, 3];
    let keep = &fixed[0];
    mutate(fixed);
    print(fixed.len, ",", fixed[0], ",", fixed[1], ",", fixed[2], ",", keep);
    assert(keep .== &fixed[0]);
    var limited: u8[..4] = [7, 8];
    let old = &limited[0];
    append(limited, 9);
    print(limited.len, ",", limited.cap, ",", limited[2], ",", old);
    print(limited.pop(), ",", limited.len, ",", old);
    limited.clear(); limited.push(42);
    for &v, i in limited { v += i as! u8; }
    print(limited.len, ",", limited[0]);
    var medium: f32[..256] = [-0.0, 1.5];
    print(medium.len, ",", medium.cap, ",", medium[0], ",", medium.pop());
    medium.push(2.5); print(medium[1]);
    var zero: u8[0] = []; empty(zero);
    var no_capacity: bool[..0] = []; print(no_capacity.len, ",", no_capacity.cap);
    var link: i16[3]? = null;
    print(link == null); link .= fixed; print(link.len, ",", link[2]);
    global_limited.push(33);
    print(global_fixed[0], ",", global_fixed[1], ",", global_fixed[2]);
    print(global_limited.len, ",", global_limited.cap, ",", global_limited[0], ",", marker);
}
