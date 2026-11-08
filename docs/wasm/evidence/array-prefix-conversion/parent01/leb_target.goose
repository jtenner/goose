fn main(){var a:u8[u16]=[1,2,3];var b:u8[varint]=copy(a);assert(b.len==3&&b[0]==1&&b[2]==3);print("leb_target");}
