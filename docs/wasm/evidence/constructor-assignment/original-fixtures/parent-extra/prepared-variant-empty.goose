enum E { Value { n: i64 }, Empty }
fn main() { var a: E.Empty = E.Empty; var b: E.Empty = E.Empty; a = E.Empty; assert(&a .!= &b); print("variant-empty"); }
