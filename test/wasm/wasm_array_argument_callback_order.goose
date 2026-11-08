var value:i64[2]=[3,4];recursive fn later()->i64{value[0]=9;return 0;}
fn apply<F>()->i64{F(copy(value),later())}
fn main(){assert(apply(){a,x=>a[0]+x}==3);assert(value[0]==9);print("callback_order");}
