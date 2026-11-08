recursive fn probe(yes:bool)->i64{var a:u8[..3]=[7,8];var b:u8[]=if yes{return 42;}else{a};return b[1];}fn main(){assert(probe(true)==42&&probe(false)==8);print("limited_void_branch");}
