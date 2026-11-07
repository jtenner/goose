struct Numbers { flag: bool, small: f32, wide: f64, special: f64, bits: bool[2] }
struct Holder { numbers: Numbers, target: i64? }
recursive fn check(value: f64) -> f64 {
    var rows: Numbers[] = [Numbers { flag: true, small: -0.0 as f32, wide: value, special: 0.0 / 0.0, bits: [true, false] },
                          Numbers { flag: false, small: 16777217.0 as f32, wide: -value, special: 0.0 / 0.0, bits: [false, true] }];
    assert(rows[0].flag); assert(!rows[1].flag);
    assert(rows[0].bits[0]); assert(!rows[0].bits[1]); assert(rows[1].bits[1]);
    assert(1.0 / rows[0].small < 0.0); assert(rows[1].small == 16777216.0);
    assert(rows[0].special != rows[0].special);
    var copied: Numbers[] = copy(rows); copied[0].wide += 1.0;
    assert(rows[0].wide == value); assert(copied[0].wide == value + 1.0);
    assert(1.0 / copied[0].small < 0.0); assert(copied[1].special != copied[1].special);
    return copied[1].wide;
}
fn main() {
    assert(check(7.0) == -7.0);
    var x: i64[] = [41]; assert(check(9.0) == -9.0);
    var template: Numbers = Numbers { flag: true, small: 1.25 as f32, wide: -2.5, special: 0.0 / 0.0, bits: [false, true] };
    var holders: Holder[] = [Holder { numbers: template }, Holder { numbers: template, target: x[0] }];
    var absent: i64? = holders[0].target; assert(absent == null);
    var present: i64? = holders[1].target;
    if present { present += 1; } else { assert(false); }
    assert(x[0] == 42); holders[0].target .= x[0];
    var copied: Holder[] = copy(holders);
    var selected: i64? = copied[0].target;
    if selected { selected += 2; } else { assert(false); }
    assert(x[0] == 44); assert(copied[1].numbers.flag); assert(copied[1].numbers.small == 1.25);
    assert(copied[0].numbers.special != copied[0].numbers.special); assert(copied[0].numbers.bits[1]);
    print("data-mixed=ok");
}
