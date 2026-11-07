struct S { n:i64=7 }
struct H { rows:S[2] }
recursive fn replace(dst:H&) { dst=H{rows:[S{n:9};2]}; }
fn main(){var a:H[]=[H{rows:default<S[2]>()},H{rows:[S{n:8};2]}];assert(a[0].rows[1].n==7);assert(a[1].rows[0].n==8);replace(a[0]);assert(a[0].rows[1].n==9);assert(a[1].rows[0].n==8);print("data_fields");}
