struct S{n:i64}
var calls:i64=0;recursive fn make(n:i64)->S{calls++;return S{n:n};}
fn main(){var sum:i64=0;for i in 4{sum+=make(i).n;}assert(sum==6);assert(calls==4);print("once_loop");}
