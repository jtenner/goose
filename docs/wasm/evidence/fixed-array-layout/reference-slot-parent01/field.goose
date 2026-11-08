struct H{a:u8[3]&}fn main(){var a:u8[3]=[1,2,3];var h=H{a};var b:u8[..4]=h.a;assert(b.len==3&&b[2]==3);print("field");}
