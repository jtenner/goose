// Adapt one array when the other operand is already a slice, in either order.
fn main() {
    let values = [1, 2];
    let x: i64;
    print(values[..] == (block { x = 2; [1] }));
    print(x);
    let y: i64;
    print((block { y = 3; [1] }) != values[..]);
    print(y);
    let z: i64;
    print([1] == (block { z = 4; values[..] }));
    print(z);
}
