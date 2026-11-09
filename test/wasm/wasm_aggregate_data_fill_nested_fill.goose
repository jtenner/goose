struct Cell { x:i16, spare:u8[..3] }
fn main() {
    var a:Cell[u64]=[Cell{x: -4,spare:[7]};2];
    assert(a.len==2 && a[0].spare.len==1 && a[1].spare[0]==7);
    a[0].spare.push(9);
    assert(a[0].spare.len==2 && a[1].spare.len==1);
    print("nested_fill");
}
