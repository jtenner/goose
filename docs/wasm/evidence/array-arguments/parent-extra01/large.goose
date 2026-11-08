recursive fn read(a:u8[70000])->i64{return a[69999];}
fn main(){var a:u8[70000]=default<u8[70000]>();a[69999]=11;assert(read(a)==11);print("large");}
