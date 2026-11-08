fn main(){var yes=true;var a:u8[..3]=[7,8];var c:u8[..3]=[9];var b:u8[]=if yes{a}else{c};assert(b.len==2&&b[1]==8);print("ok");}
