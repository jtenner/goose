struct Cell { x:i16, y:u8 }
fn main() {
    var a:Cell[u8]=[Cell{x:17,y:9};3];
    assert(a.len==3 && a[0]x:=17 && a[2]y:=9);
    a[0]x:44;
    assert(a[1]x:=17);
    print("struct_fill");
}
