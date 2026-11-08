struct S{n:i64=7}
fn main(){var a:S[1]=[S{n:1}];a=default<S[1]>();assert(a[0].n==7);print("default");}
