fn value(x: i64) -> i64 {
    var result = x;
    defer { result += 100; print("defer=", result); }
    if x > 0 { return result; }
    return 0;
}
fn noisy() -> i64 { print("inner"); return 7; }
recursive fn fib(n: i64) -> i64 {
    if n < 2 { return n; }
    return fib(n - 1) + fib(n - 2);
}
fn main() {
    var total = 0;
    for i: u8 in 0..256 {
        if i == 2 { continue; }
        if i > 4 { break; }
        total += i;
    }
    print("for=", total);
    var i = 0;
    while i < 4 {
        i++;
        defer { print("loop=", i); }
        if i == 2 { continue; }
        if i == 3 { break; }
    }
    var answer = loop { break 42; };
    let early = block { break 9; };
    print(answer, ",", early);
    print("return=", value(5));
    print("outer=", noisy());
    print("fib=", fib(10));
    var zero = 0;
    print("short=", false && (10 / zero > 0), ",", true || (10 / zero > 0));
}
