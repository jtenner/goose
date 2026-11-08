struct S{n:i64}
fn apply<F>(s:S&)->i64{F(copy(s))}
fn main(){var rows:S[]=[S{n:1}];assert(apply(rows[0]){p=>{p.n=9;p.n}}==9);assert(rows[0].n==1);print("data_callback");}
