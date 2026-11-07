var calls: i64 = 0;
fn tick() -> i64 { calls++; return calls; }
struct Arrays { first: i64 = tick(), text: u8[3], count: u16[..300], last: i64 = tick(), nil: u8[3]? }
struct Zero { a: i64[..1], n: i64 }
struct Sparse { bytes: u8[..1000000], after: i64 }
var sparse: Sparse = Sparse { bytes: [], after: 99 };
fn main() {
    var a: Arrays = Arrays { text: "a\0b", count: [4, 5] };
    print("order=", a.first, ",", a.last, ",", calls);
    a.count.push(6); a.count[0] += 3; print(a.text, ",", a.count.len, ",", a.count.cap, ",", a.count.pop());
    var b: Arrays = copy(a); b.text[0] = 90; b.count.clear(); b.count.push(10);
    print(a.text, ",", b.text, ",", a.count.len, ",", b.count[0]);
    var copied: u8[3] = copy(a.text); copied[2] = 33; print(copied, ",", a.text);
    var r: u16[..300]& = a.count; var sum: i64 = 0; for v in r { sum += v; } print("loop=", sum);
    var d: Arrays = default<Arrays>(); print("default=", d.first, ",", d.last, ",", d.text[0], ",", d.count.len, ",", d.nil);
    var z: Zero = Zero { a: [tick(); 0], n: 42 }; print("zero=", z.a.len, ",", z.n, ",", calls);
    print("sparse=", sparse.bytes.len, ",", sparse.after);
    var plain: u8[4] = default<u8[4]>(); print("plain=", plain[3]);
}
