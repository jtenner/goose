struct S{n:i64}
recursive fn make(n:i64)->S{if n>0{S{n:n}}else{S{n:9}}}
fn main(){var a:S=make(7);var b:S=make(0);assert(a.n==7);assert(b.n==9);print("if_tail");}
