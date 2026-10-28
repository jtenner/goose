// The right operand sees assignments made by the left, in source order.
fn main() {
    let x: i64;
    let y: i64;
    print((block { x = 2; print("left"); [x] }) ==
          (block { y = x + 1; print("right"); [x, y] }));
    print(x, " ", y);
    let a: i64;
    let b: i64;
    print((block { a = 4; [a] }) != (block { b = a + 1; [a, b] }));
    print(a, " ", b);
}
