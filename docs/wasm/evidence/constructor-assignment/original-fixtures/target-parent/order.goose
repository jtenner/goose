struct S { n: i64 }
struct Outer { value: S }
struct Control { target: Outer& }
var trace: i64 = 0;
recursive fn value(control: Control&, replacement: Outer&) -> i64 { control.target .= replacement; trace = trace * 10 + 2; return 77; }
recursive fn left() -> i64 { trace = trace * 10 + 1; return 0; }
fn main() {
 var first: Outer = Outer { value: S { n: 1 } }; var second: Outer = Outer { value: S { n: 2 } };
 var control: Control = Control { target: first };
 control.target.value = S { n: value(control, second) };
 assert(first.value.n == 77); assert(second.value.n == 2); assert(control.target .== &second);
 trace = 0; var rows: S[] = [S { n: 1 }]; rows[left()] = S { n: value(control, first) };
 assert(trace == 12); assert(rows[0].n == 77); print("order");
}
