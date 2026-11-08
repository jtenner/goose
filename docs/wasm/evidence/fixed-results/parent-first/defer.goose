struct S{n:i64}
recursive fn make()->S{var s:S=S{n:7};defer{s.n=9;}return s;}
fn main(){var s:S=make();assert(s.n==7);print("defer");}
