// error: cannot assign to let x (§4.4)
// Two actual assignments must still fail, including across the operands.
fn main() {
    let x: i64;
    print((block { x = 1; [1] }) == (block { x = 2; [1, 2] }));
}
