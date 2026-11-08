struct S { n:i64 }
var index:i64 = 1;
recursive fn make()->S { print("rhs"); return S { n:9 }; }
fn main() { var rows:S[]=[S { n:1 }]; print("before"); rows[index]=make(); print("after"); }
