fn main(){var a:u8[u8]=[1,2,3];var r:u8[u8]& =a;var b:u8[u16]=copy(r);assert(b.len==3&&b[0]==1&&b[2]==3);print("reference");}
