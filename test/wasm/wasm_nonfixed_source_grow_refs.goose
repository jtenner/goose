fn main(){var n:i64=7;var a:i64&[>..]=[n,n];var b:i64&[u16]=copy(a);assert(b.len==2&&b[0]==7);b[1]=31;assert(n==31&&a[0]==31);print("grow_refs");}
