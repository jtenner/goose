recursive fn take(a:u8[2147483648],b:u8[2147483648])->i64{return a[0]+b[0];}
fn main(){var x:u8[2147483648]=default<u8[2147483648]>();print(take(x,x));}
