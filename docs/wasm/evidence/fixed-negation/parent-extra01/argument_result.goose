struct S{x:i64,y:i64}
recursive fn sum(s:S)->i64{return s.x+s.y;}
recursive fn neg(s:S&)->S{return -s;}
fn main(){var s:S=S{x:7,y:8};assert(sum(-s) == -15);var n:S=neg(s);assert(n.x == -7);assert(s.x==7);print("argument_result");}
