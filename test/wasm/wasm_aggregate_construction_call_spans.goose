struct S{n:i64}
struct H{rows:S[2]}
recursive fn build(n:i64)->i64{var a:H[]=[H{rows:[S{n:n};2]}];return a[0].rows[1].n;}
fn main(){assert(build(1)==1);var outer:H[]=[H{rows:[S{n:7};2]}];assert(build(2)==2);assert(outer[0].rows[1].n==7);{var more:H[]=[H{rows:[S{n:9};2]}];assert(build(3)==3);assert(more[0].rows[0].n==9);assert(outer[0].rows[0].n==7);}print("call_spans");}
