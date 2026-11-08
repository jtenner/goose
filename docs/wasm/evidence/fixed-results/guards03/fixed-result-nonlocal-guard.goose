struct S{n:i64}
var calls:i64=0;
inline fn invoke<F>(a:S)->S{defer{calls++;}return F(a); }
recursive fn make(n:i64)->S{return invoke(S{n:n}){p=>if p.n==7{return S{n:9};}S{n:p.n}};}
fn main(){var a:S=make(7);var b:S=make(3);assert(a.n==9);assert(b.n==3);assert(calls==2);print("callback_exit");}
