struct S{n:i64}
var calls:i64=0;
inline fn make(early:bool)->S{defer{calls++;}if early{return S{n:7};}return S{n:9};}
fn main(){var a:S=make(true);var b:S=make(false);assert(a.n==7);assert(b.n==9);assert(calls==2);print("inline_early");}
