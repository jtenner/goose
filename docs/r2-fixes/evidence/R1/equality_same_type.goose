fn main() {
    let x: i64;
    print([1, 2] == (block { x = 2; [1, 2] }));
    print(x);
}
