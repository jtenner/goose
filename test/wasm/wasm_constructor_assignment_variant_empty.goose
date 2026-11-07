enum E { Value { n: i64 }, Empty }
fn main() { var a: E.Empty = default<E.Empty>(); var b: E.Empty = default<E.Empty>(); a = default<E.Empty>(); assert(&a .!= &b); print("variant-empty"); }
