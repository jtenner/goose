struct S{link:i64&}
recursive fn make(p:i64&)->S{return S{link:p};}
fn main(){var a:i64[]=[7];assert(make(a[0]).link .== &a[0]);print("ref_compare");}
