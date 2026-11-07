struct S {}
fn main() { var a: S = S {}; var b: S = S {}; a = S {}; assert(&a .!= &b); print("empty"); }
