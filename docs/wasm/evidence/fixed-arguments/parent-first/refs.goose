struct S{n:i64,link:i64&}
recursive fn alter(s:S)->i64{s.n=9;s.link+=1;return s.n;}
fn main(){var x:i64[]=[7];var a:S=S{n:2,link:x[0]};assert(alter(a)==9);assert(a.n==2);assert(x[0]==8);assert(a.link .== &x[0]);print("refs");}
