recursive fn make(n:i64)->i64[2]{if n==0{return[1,2];}var a:i64[2]=make(n-1);return[a[0]+n,a[1]+n];}
fn main(){var a:i64[2]=make(9);assert(a[0]==46);assert(a[1]==47);print("recursion");}
