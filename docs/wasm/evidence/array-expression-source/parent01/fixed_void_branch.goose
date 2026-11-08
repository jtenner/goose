recursive fn probe(yes:bool)->i64{var a:u8[2]=[7,8];var b:u8[]=if yes{return 42;}else{a};return b[1];}fn main(){assert(probe(true)==42&&probe(false)==8);print("fixed_void_branch");}
