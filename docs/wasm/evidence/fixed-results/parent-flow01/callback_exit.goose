struct S{n:i64}
var calls:i64=0;
inline fn invoke<F>(a:S)->S{defer{calls++;}return F(a);}
recursive fn make(early:bool)->S{return invoke(S{n:7}){p=>if early{return S{n:9};}S{n:p.n}};}
fn main(){var a:S=make(true);var b:S=make(false);assert(a.n==9);assert(b.n==7);assert(calls==2);print("callback_exit");}
