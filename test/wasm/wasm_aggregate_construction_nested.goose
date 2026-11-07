struct S { n:i64=7 }
struct H { rows:S[2] }
fn main(){var a:H=H{rows:default<S[2]>()};assert(a.rows[1].n==7);a=H{rows:[S{n:9};2]};assert(a.rows[0].n==9);assert(a.rows[1].n==9);print("nested");}
