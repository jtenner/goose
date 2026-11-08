struct S{n:i64}
var calls:i64=0;recursive fn tick()->i64{calls++;return 7;}
recursive fn choice(flag:bool)->bool{return flag;}
fn main(){assert(({let n=tick();S{n:n}}).n==7);assert((if choice(true){S{n:tick()}}else{S{n:9}}).n==7);assert(({let n=tick();[n,n+1]})[1]==8);assert(calls==3);print("block_roots");}
