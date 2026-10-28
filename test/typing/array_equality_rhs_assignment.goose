// A single assignment remains single when different array sizes compare as slices.
fn main() {
    let x: i64;
    print([1] == (block { x = 2; [1, 2] }));
    print(x);
    let y: i64;
    print([1] != (block { y = 3; [1, 2] }));
    print(y);
}
