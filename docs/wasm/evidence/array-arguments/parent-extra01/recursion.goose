recursive fn fold(a:i64[2],n:i64)->i64{if n==0{return a[0];}a[0]+=n;let saved=a[0];var result:i64=fold(a,n-1);assert(a[0]==saved);return result;}
fn main(){var a:i64[2]=[3,4];assert(fold(a,3)==9);assert(a[0]==3);print("recursion");}
