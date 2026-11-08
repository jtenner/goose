recursive fn make(p:i64&)->i64&[2]{return[p,p];}
fn main(){var a:i64[]=[7];assert(make(a[0])[1] .== &a[0]);print("array_ref_identity");}
