struct S{n:i64}recursive fn run(depth:i64)->i64{{var a:S[u16]=[S{depth};2];assert(a[1].n==depth);}if depth>0{return run(depth-1)+depth;}return 0;}fn main(){assert(run(4)==10);print("recursive");}
