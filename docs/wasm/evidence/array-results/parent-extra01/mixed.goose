struct S{n:i64}
recursive fn make(s:S,a:i64[2])->i64[2]{return[s.n+a[0],s.n+a[1]];}
fn main(){var s:S=S{n:5};var a:i64[2]=[3,4];var b:i64[2]=make(s,a);assert(b[0]==8);assert(b[1]==9);print("mixed");}
