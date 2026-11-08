struct S{n:i64}
recursive fn read(a:S[2])->i64{return a[0].n+a[1].n;}
fn main(){var a:S[2]=[S{n:3},S{n:4}];assert(read(a)==7);print("nominal");}
