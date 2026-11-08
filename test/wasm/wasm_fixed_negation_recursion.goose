struct S{x:i64,y:i64}
recursive fn make(n:i64)->S{if n==0{return S{x:1,y:2};}return -make(n-1);}
fn main(){var a:S=make(4);var b:S=make(3);assert(a.x==1);assert(b.y == -2);print("recursion");}
