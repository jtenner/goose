struct S{n:i64}
recursive fn walk(s:S,depth:i64)->i64{if depth==0{return s.n;}var next:S=S{n:s.n+1};var result:i64=walk(next,depth-1);assert(next.n==s.n+1);return result;}
fn main(){var a:S=S{n:1};assert(walk(a,3)==4);assert(a.n==1);print("recursion");}
