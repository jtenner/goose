enum E{A{n:i64},B}
recursive fn read(e:E)->i64{var result:i64=0;match e{A p=>{result=p.n;},B=>{result=7;}}return result;}
fn main(){var a:E=E.A{n:9};assert(read(a)==9);assert(read(E.B)==7);print("enum");}
