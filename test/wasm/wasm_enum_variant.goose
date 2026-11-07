var calls: i64 = 0; fn tick() -> i64 { calls++; return calls; }
enum V { Items { before: u8, values: u16[..3], bytes: u8[3], zero: i64[..1], flag: bool, real: f64, after: u16 }, Empty }
fn main() {
 var v: V.Items = V.Items { before: 7, values: [1, 2], bytes: "a\0b", zero: [tick(); 0], flag: false, real: 1.5, after: 65000 };
 v.values.push(3); var r: u16[..3]& = v.values; var sum: i64 = 0; for n in r { sum += n; } assert(sum == 6); assert(v.values.pop() == 3); assert(v.before == 7); assert(v.after == 65000); v.values.clear(); assert(v.values.len == 0);
 var bit: bool = &v.flag; var real: f64 = &v.real; assert(!bit); assert(real == 1.5); assert(v.zero.len == 0); assert(calls == 1); print(v.bytes, ",", sum);
}
