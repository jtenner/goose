struct S{n:i64}
fn main(){var a:S[..70000]=[S{n:7};2];assert(a.len==2);assert(a[1].n==7);print("prefix32");}
