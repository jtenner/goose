var calls: i64 = 0;
fn index() -> i64 { calls += 1; return 0; }
fn main() {
    var a: i64[3] = [1, 2, 3]; var b: i64[3] = [10, 20, 30];
    var owners: i64[3]&[2] = [a, b];
    for value in owners[index()] { print(value); owners[0] .= b; }
    print("calls=", calls);
    owners[0] .= a;
    var which: i64 = 0;
    for value in owners[which] { print(value); which = 1; }
}
