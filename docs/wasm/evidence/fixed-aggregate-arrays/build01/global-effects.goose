struct S { n: i64 }
var observed: i64 = 0;
fn inspect() -> i64 { observed = observed * 10 + rows.len; return rows.len; }
var rows: S[..3] = [S { n: inspect() }, S { n: inspect() }];
fn main() { print("global=", observed, ",", rows[0].n, ",", rows[1].n, ",", rows.len); }
