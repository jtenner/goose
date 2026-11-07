enum E { A{n:i64=7},B }
fn main(){var a:E[2]=default<E[2]>();match a[1]{A p=>assert(p.n==7),_=>assert(false)}var b:E[2]=[E.B;2];match b[0]{B=>{},_=>assert(false)}print("enums");}
