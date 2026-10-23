// dump-runtime: both arms parse; only the selected branch is checked.
let CHOICE = true;
fn pick<T>(value: T) -> T {
    const if CHOICE { value } else { unavailable(value); }
}
fn main() {
    print(pick(42));
    const for <N> in [true, false] {
        const if N { print("yes"); } else { print("no"); }
    }
    const if false { let x: ns::Unknown = ns::Unknown {}; }
}
