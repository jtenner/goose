struct S{n:i64}
recursive fn make()->S{return S{7};}
recursive fn noise()->i64{var s:S=S{99};return s.n;}
recursive fn read(p:i64&?,x:i64)->i64{if p{return p;}return 0;}
fn apply<F>()->i64{read(F(make().n),noise())}
fn main(){assert(apply(){p:i64&? =>p}==7);print("optional");}
