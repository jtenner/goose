struct S{link:i64&?}
recursive fn make(p:i64&?)->S{return S{link:p};}
fn main(){assert(make(null).link==null);print("ref_null");}
