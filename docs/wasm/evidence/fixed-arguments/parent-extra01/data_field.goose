struct S{n:i64}
struct H{s:S}
recursive fn read(p:S)->i64{p.n++;return p.n;}
fn main(){var rows:H[]=[H{s:S{n:7}}];assert(read(rows[0].s)==8);assert(rows[0].s.n==7);print("data_field");}
