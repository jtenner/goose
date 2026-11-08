fn main(){var a:u8[3]=[1,2,3];var refs:u8[3]&[1]=[a];var b:u8[..4]=refs[0];assert(b.len==3&&b[2]==3);print("indexed");}
