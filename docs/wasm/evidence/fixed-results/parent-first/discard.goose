struct S{n:i64}
var calls:i64=0;recursive fn make()->S{calls++;defer{calls++;}return S{n:7};}
fn main(){make();assert(calls==2);print("discard");}
