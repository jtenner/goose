struct Cell { value: i64 }
struct Big { bytes: u8[70000], last: i64 }
fn grow(a: Cell&) -> i64 {
    var big: Big = Big { bytes: [7; 70000], last: 99 };
    a.value += big.bytes[69999]; return big.last;
}
fn helper(a: Cell&, early: bool) -> i64 {
    var local: Cell = copy(a);
    defer { print("defer=", local.value); var data: i64[] = [9]; print(data[0]); }
    if early { return local.value; } local.value += 1; return local.value;
}
fn main() {
    var a: Cell = Cell { value: 10 }; var pointer: i64& = a.value;
    print(grow(a), ",", pointer, ",", a.value);
    print(helper(a, true)); print(helper(a, false));
    for i in 3 {
        var b: Cell = copy(a); defer { print("loop=", i, ",", b.value); }
        if i == 0 { continue; } if i == 1 { break; }
    }
    print("source=", a.value);
}
