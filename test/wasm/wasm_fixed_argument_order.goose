struct S{n:i64}
recursive fn change(s:S&)->i64{s.n=9;return 0;}
recursive fn read(s:S,unused:i64)->i64{return s.n+unused;}
fn main(){var a:S=S{n:2};assert(read(a,change(a))==2);assert(a.n==9);print("order");}
