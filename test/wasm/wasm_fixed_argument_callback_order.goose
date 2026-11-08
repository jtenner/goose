struct S{n:i64}
var original:S=S{n:7};recursive fn later()->i64{original.n=12;return 0;}
fn apply<F>()->i64{F(copy(original),later())}
fn main(){assert(apply(){p,x=>p.n+x}==7);assert(original.n==12);print("callback_order");}
