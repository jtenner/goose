struct S{n:i64}
fn main(){var a:S[2]=[S{n:1},S{n:2}];var b:S[2]=[S{n:7},S{n:8}];a=b;assert(a[0].n==7);assert(a[1].n==8);print("nominal");}
