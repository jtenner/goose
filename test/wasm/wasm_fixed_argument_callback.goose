struct S{n:i64}
fn apply<F>(s:S&)->i64{F(copy(s))}
fn main(){var a:S=S{n:7};var n:i64=apply(a){p=>p.n};assert(n==7);print("callback");}
