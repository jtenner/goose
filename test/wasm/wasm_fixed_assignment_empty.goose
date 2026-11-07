struct S {}
fn main() { var a: S = S {}; var b: S = S {}; a = b; assert(&a .!= &b); print("empty"); }
