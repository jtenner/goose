// The left operand's assignment must also run once during slice adaptation.
fn main() {
    let x: i64;
    print((block { x = 2; [1] }) == [1, 2]);
    print(x);
    let y: i64;
    print((block { y = 3; [1] }) != [1, 2]);
    print(y);
}
