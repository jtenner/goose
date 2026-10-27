// error: defer takes a statement or a block, not `const`
fn main() {
    defer const X = 1;
}
