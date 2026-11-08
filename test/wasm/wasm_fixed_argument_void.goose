struct S{n:i64}
recursive fn set(p:S,out:i64&){p.n=9;out=p.n;}
fn main(){var s:S=S{n:2};var out:i64=0;set(s,out);assert(out==9);assert(s.n==2);print("void");}
