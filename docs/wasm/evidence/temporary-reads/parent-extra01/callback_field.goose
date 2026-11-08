struct S{n:i64}
fn apply<F>(n:i64)->i64{F(n).n}
fn main(){assert(apply(7){n=>S{n:n}}==7);print("callback_field");}
