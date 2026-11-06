fn nested(x: f32) -> f64 { { x } }
fn conditional(b: bool, x: f32, y: f32) -> f64 { if b { x } else { y } }
fn early(x: f32) -> f64 { block { x } }
recursive fn both(b: bool, p: i64?) -> bool { return b && p; }
recursive fn either(b: bool, p: i64?) -> bool { return b || p; }
recursive fn return_in_print(b: bool) -> i64 {
    print("unused", if b { return 3; } else { 4 });
    return 0;
}
fn change(x: i64&) -> i64 { x += 1; return 8; }
fn main() {
    print(nested(0.1));
    print(conditional(true, 0.1, 0.2));
    print(conditional(false, 0.1, 0.2));
    print(early(0.1));
    var n = 7;
    let p: i64? = &n;
    let absent: i64? = null;
    print(both(true, p) == true, ",", either(false, p) == true);
    print(both(true, absent) == false, ",", either(false, absent) == false);
    print(p, ",", absent);
    print(p, ",", change(n));
    for i in 10 { return_in_print(true); }
    print("done");
}
