struct S { n: i64 }
var trace: i64 = 0;
recursive fn left() -> i64 { trace = trace * 10 + 1; return 0; }
recursive fn right(value: S&) -> S& { trace = trace * 10 + 2; return value; }
fn main() { var rows: S[] = [S { n: 1 }]; var value: S = S { n: 2 }; rows[left()] = right(value); assert(trace == 12); assert(rows[0].n == 2); print("order"); }
