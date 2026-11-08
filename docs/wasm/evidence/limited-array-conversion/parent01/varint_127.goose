fn main(){var a:u8[..65536]=[];for i in 0..127{a.push(i as u8);}var b:u8[varint]=a;assert(b.len==127&&b[126]==126);print("varint_127");}
