struct S{n:i64=7}
struct H{rows:S[..3]}
fn main(){var a:H[]=[H{rows:default<S[2]>()}];assert(a[0].rows.len==2);assert(a[0].rows[1].n==7);print("data");}
