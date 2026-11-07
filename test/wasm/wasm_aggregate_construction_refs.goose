struct S { link:i64& }
fn main(){var x:i64[]=[7];var old:S=S{link:x[0]};var a:S[2]=[old;2];assert(a[0].link .== &x[0]);assert(a[1].link .== &x[0]);a[1].link=9;assert(x[0]==9);assert(old.link==9);print("refs");}
