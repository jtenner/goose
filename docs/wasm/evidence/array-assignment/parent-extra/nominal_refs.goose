struct S{link:i64&}
fn main(){var x:i64[]=[1];var y:i64[]=[7];var a:S[2]=[S{link:x[0]},S{link:x[0]}];var b:S[2]=[S{link:y[0]},S{link:y[0]}];a=b;assert(a[1].link .== &y[0]);a[0].link=9;assert(y[0]==9);assert(x[0]==1);print("nominal_refs");}
