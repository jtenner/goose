struct S{n:i64}
var original:S=S{n:7};recursive fn later()->i64{original.n=12;return 0;}
inline fn read(p:S,x:i64)->i64{let saved=p.n;p.n=9;return saved+x;}
fn main(){assert(read(original,later())==7);assert(original.n==12);print("inline_order");}
