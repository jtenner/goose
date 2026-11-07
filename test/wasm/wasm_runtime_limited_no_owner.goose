fn inspect(a: const u8[..]?) { print("optional=", a); }
fn main() { var none: const u8[..]? = null; inspect(none); }
