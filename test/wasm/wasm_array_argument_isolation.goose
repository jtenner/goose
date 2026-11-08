recursive fn read(a:i64[2],b:i64[2],original:i64[2]&)->i64{assert(&a .!= &b);assert(&a .!= original);a[0]=9;assert(b[0]==3);assert(original[0]==3);return a[0];}
fn main(){var a:i64[2]=[3,4];assert(read(a,a,a)==9);assert(a[0]==3);print("isolation");}
