struct S { value: i64& }
fn main() { var old: i64[] = [1]; var next: i64[] = [7]; var holder: S = S { value: old[0] }; { var source: S = S { value: next[0] }; holder = source; } var scratch: i64[] = [99]; holder.value += 1; assert(next[0] == 8); assert(scratch[0] == 99); print("outer"); }
