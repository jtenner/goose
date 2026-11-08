struct S{n:i64}
fn main(){var a:S[2]=[S{n:1},S{n:2}];a=[S{n:9};2];assert(a[0].n==9);assert(a[1].n==9);print("fill");}
