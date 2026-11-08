struct S{n:i64}
recursive fn effect()->i64{print("effect");return 1;}
recursive fn use(p:S,x:i64)->i64{return p.n+x;}
recursive fn run()->i64{return use(S{n:effect()},{return 7;8});}
fn main(){assert(run()==7);print("always_return");}
