struct S{n:i64}
inline fn make(n:i64)->S{if n==0{return S{n:3};}return S{n:n};}
fn apply<F>(n:i64)->S{-F(n)}
fn main(){var a:S=-make(0);assert(a.n == -3);var b:S=apply(7){n=>S{n:n}};assert(b.n == -7);print("inline_callback");}
