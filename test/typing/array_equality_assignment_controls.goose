// Equal array types need no adaptation. Binding the right value first is valid too.
fn main() {
    let x: i64;
    print([1, 2] == (block { x = 2; [1, 2] }));
    print(x);
    let y: i64;
    let rhs = block { y = 2; [1, 2] };
    print([1] == rhs);
    print(y);
    let n: i64;
    print((block { n = 7; n }) == n);
    print(n);
    let flag: bool;
    print((block { flag = true; flag }) != false);
}
