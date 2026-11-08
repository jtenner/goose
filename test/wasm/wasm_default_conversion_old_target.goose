struct S{n:i64=observe()}
struct H{rows:S[..3]}
var target:H=H{rows:[S{n:9}]};
recursive fn observe()->i64{return target.rows.len;}
fn main(){target=H{rows:default<S[2]>()};assert(target.rows.len==2);assert(target.rows[0].n==1);assert(target.rows[1].n==1);print("old_target");}
