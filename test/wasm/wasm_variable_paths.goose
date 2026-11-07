fn temporary(n: i64) -> i64 {
    var scratch: i64[u8] = [99]; print("temporary=", scratch[0]); return n;
}
fn main() {
    print(temporary(0));
    var a: i64[] = [1]; var b: i64[] = [10, 20, 30];
    var owners: i64[]&[u8] = [a];
    for v in owners[0] { print("path=", v); owners[0] .= b; }
    var values: i64[] = [temporary(4), temporary(5)];
    print(values.len, ",", values[0], ",", values[1]);
    var optional: i64[]? = null; print(optional == null); optional .= b;
    print(optional.len, ",", optional[2]);
    var total: i64 = 0;
    for i in 10000 { var scoped: i64[u16] = [i, i + 1]; total += scoped[0]; }
    print("total=", total);
}
