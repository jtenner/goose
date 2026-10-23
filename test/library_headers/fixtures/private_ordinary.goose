struct PrivateOrdinary { prefix: u8, value: u32 }
recursive fn ident<T>(v: T) -> T { v }
export fn api() -> u32 { ident(PrivateOrdinary { 1, 42 }).value }
