// dump-runtime: flatten conditional initializers before named/positional checks.
let EXTRA = true;
struct S { a: u32, const if EXTRA { b: u64 = 8, } else {}, z: u32 = 3 }
fn main() {
    let a = S { a: 1, const if EXTRA { b: 2, } else {}, z: 4 };
    let b = S { 1, const if EXTRA { 2, } else {}, 4 };
    print(a == b);
    let c = S { a: 1, const if false { bad: ns::Unknown {}, }, };
    print(c.b, " ", c.z);
    const for <K> in [true, false] {
        let d = S { a: 1, const if K { z: 7, } else { z: 9, }, };
        print(d.z);
    }
}
