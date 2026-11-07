struct S { n: i64 }
struct Outer { value: S }
struct Control { target: Outer& }
var source: S = S { n: 77 };
recursive fn get(control: Control&, replacement: Outer&) -> S& { control.target .= replacement; return source; }
fn main() { var first: Outer = Outer { value: S { n: 1 } }; var second: Outer = Outer { value: S { n: 2 } }; var control: Control = Control { target: first }; control.target.value = get(control, second); assert(first.value.n == 77); assert(second.value.n == 2); assert(control.target .== &second); print("effects"); }
