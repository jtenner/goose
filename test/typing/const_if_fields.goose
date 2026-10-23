// dump-runtime: effective fields retain declaration order and packed layout.
let EXTRA = true;
struct Selected<T> {
    a: u32 = 1,
    const if EXTRA {
        let b: u64 = 2,
        const if false { absent: ns::Missing, absent: ns::Missing, }
        else { pad 1, },
    } else { absent: ns::Unknown, },
    z: T = 3,
}
struct Empty { const if false { bad: ns::Unknown, } }
fn main() {
    let x = Selected<u32> {};
    const for <N, A> in fields<Selected<u32>> { print(N, "=", x.A); }
    print(bytes_of([x]).len);
    print(bytes_of([Empty {}, Empty {}]).len);
}
