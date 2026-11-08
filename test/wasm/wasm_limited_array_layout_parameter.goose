recursive fn take(a:u8[..256])->i64{return a.len+a[1];}fn main(){var a:u8[..3]=[7,8];assert(take(a)==10);print("parameter");}
