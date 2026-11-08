fn main(){var a:u8[u8]=[73;0];var b:u8[u16]=copy(a);assert(b.len==0&&a.len==0);print("empty");}
