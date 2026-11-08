struct S{n:i64=7}
struct H{a:S[1]}
fn main(){var h:H=H{a:[S{n:1}]};h.a=[S{n:9}];assert(h.a[0].n==9);print("nested");}
