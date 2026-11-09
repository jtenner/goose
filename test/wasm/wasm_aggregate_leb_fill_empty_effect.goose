struct Cell { x:i64 }
fn next(n:i64&) -> Cell { n+=1; return Cell{x:n}; }
fn main() {
    var n:i64=0;
    var a:Cell[varint]=[next(n);0];
    assert(a.len==0 && n==1);
    print("empty_effect");
}
