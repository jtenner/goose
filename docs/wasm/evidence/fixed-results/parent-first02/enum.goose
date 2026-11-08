enum E{A{n:i64},B}
recursive fn make(n:i64)->E{if n==0{return E.B;}return E.A{n:n};}
fn main(){var a:E=make(7);var b:E=make(0);var sum:i64=0;match a{A p=>{sum+=p.n;},B=>assert(false)}match b{A p=>assert(false),B=>{sum++;}}assert(sum==8);print("enum");}
