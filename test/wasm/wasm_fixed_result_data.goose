struct S{n:i64}
struct H{s:S}
recursive fn make(n:i64)->S{return S{n:n};}
fn main(){var rows:H[]=[H{s:make(7)}];assert(rows[0].s.n==7);rows[0].s=make(9);assert(rows[0].s.n==9);print("data");}
