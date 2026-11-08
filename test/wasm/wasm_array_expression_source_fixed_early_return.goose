recursive fn probe(yes:bool)->i64{var b:u8[]=({if yes{return 42;}var a:u8[2]=[7,8];a});return b[1];}fn main(){assert(probe(true)==42&&probe(false)==8);print("fixed_early_return");}
