struct S{n:i64}
var s:S=S{n:7};var a:i64[2]=[7,8];
recursive fn index()->i64{a[1]=99;return 1;}
fn main(){assert(copy(s).n==7);assert(default<S>().n==0);assert(copy(a)[index()]==8);assert(a[1]==99);print("copy_root");}
