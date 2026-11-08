enum E{A{n:i64=7},B}
recursive fn read(p:E.A)->i64{return p.n;}
fn main(){var a:E.A=default<E.A>();assert(read(a)==7);print("variant");}
