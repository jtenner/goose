recursive fn change(a:i64&[2]){a[1]+=1;}
fn main(){var a:i64=3;var b:i64=4;var refs:i64&[2]=[&a,&b];change(refs);assert(a==3);assert(b==5);print("refs");}
