fn main(){var a:u8[..0];var b:u8[..256]=a;assert(b.len==0);b.push(7);assert(b[0]==7);print("zero_up");}
