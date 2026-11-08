recursive fn read(a:u16[..4]&) -> i64 { var b:u16[..4]=[]; b=a; return b.len; }
fn main(){var a:u16[..2]=[1,2];assert(read(a)==2);print("view");}
