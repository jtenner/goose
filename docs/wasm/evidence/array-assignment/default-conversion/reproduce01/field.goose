struct S{n:i64=7}
struct H{rows:S[..3]}
fn main(){var h:H=H{rows:default<S[2]>()};print(h.rows.len);}
