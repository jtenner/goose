struct S{n:i64=7}
fn main(){var a:S[..300]=default<S[2]>();assert(a.len==2);assert(a[1].n==7);print("prefix16");}
