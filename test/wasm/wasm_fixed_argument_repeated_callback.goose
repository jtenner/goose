struct S{n:i64}
fn twice<F>(s:S&)->i64{F(copy(s))+F(copy(s))}
fn main(){var s:S=S{n:1};assert(twice(s){p=>{p.n++;p.n}}==4);assert(s.n==1);print("repeated_callback");}
