struct ApiInner { value: u32 }
struct ApiPacked { prefix: u8, inner: ApiInner, values: u16[2] }
// A type only reached through an exported reference needs a complete body.
struct ApiRefOnly { value: u32 }
// An element only reached through a slice also needs its body.
struct ApiSliceOnly { value: u32 }
enum ApiChoice { Some { value: u32 }, None }
struct PrivateOrdinary { value: u32 }
recursive fn ident<T>(v: T) -> T { v }
export fn api() -> u32 { ident(PrivateOrdinary { 42 }).value }
export fn scalar(a: i32, b: f64, c: bool) -> f64 { a + b + (if c { 1 } else { 0 }) }
export fn packed(v: ApiPacked) -> ApiPacked { v }
export fn reference(v: const ApiRefOnly&) -> u32 { v.value }
export fn slices(v: const ApiSliceOnly[:]) -> u32 { v[0].value }
export fn choose(v: ApiChoice) -> ApiChoice { v }
export fn text() -> const u8[:] { "header" }
