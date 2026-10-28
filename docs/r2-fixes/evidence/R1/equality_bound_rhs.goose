fn main() {
    let x: i64;
    let rhs = (block { x = 2; [1, 2] });
    print([1] == rhs);
    print(x);
}
