var ga: i64[3] = [1, 2, 3];
var gb: i64[3] = [10, 20, 30];
var row_a: i64[3]&[1] = [ga];
var row_b: i64[3]&[1] = [gb];
var current_row: i64[3]&[1]& = row_a;
var calls: i64 = 0;
fn change() -> i64 { current_row .= row_b; calls += 1; return 0; }
fn pick(a: i64[3]&[1]&) -> i64[3]&[1]& { calls += 1; return a; }
fn main() {
    for value in current_row[0] { print(value); current_row .= row_b; }
    current_row .= row_a;
    for value in current_row[change()] { print(value); row_a[0] .= gb; }
    print("calls=", calls);
    row_a[0] .= ga;
    for value in pick(row_a)[0] { print(value); row_a[0] .= gb; }
    print("calls=", calls);
    var x: i64[3] = [100, 200, 300]; var y: i64[3] = [400, 500, 600];
    var rows: i64[3]&[1] = [x];
    var nested: i64[3]&[1]&[1] = [rows];
    for &value in nested[0][0] { value += 1; rows[0] .= y; }
    print(x[0], ",", x[1], ",", y[1], ",", y[2]);
}
