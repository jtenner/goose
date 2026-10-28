// error: variable x may be used before it is assigned
// A right operand cannot initialize a variable read by the left operand.
fn main() {
    let x: i64;
    print([x] == (block { x = 2; [1, 2] }));
}
