struct S{n:i64}
struct H{s:S,a:i64[2]}
recursive fn make(n:i64)->H{return H{s:S{n:n},a:[n,n+1]};}
fn main(){var s:S=S{n:0};var a:i64[2]=[0,0];s=make(7).s;a=make(8).a;assert(s.n==7);assert(a[0]==8);assert(a[1]==9);print("assign_projection");}
