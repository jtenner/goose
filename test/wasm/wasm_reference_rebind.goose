var global: i64 = 11;
var other: i64 = 20;
var global_ref = &global;
fn main() {
    var a = 1;
    var b = 2;
    var r = &a;
    r .= b;
    r += 3;
    let alias .= r;
    alias += 1;
    print(a, ",", b, ",", r);
    global_ref .= other;
    global_ref += 1;
    print(global, ",", other);
    var optional: i64? = a;
    optional .= null;
    print(optional == null);
}
