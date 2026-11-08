fn main(){var a:u8[..65536]=[];for i in 0..128{a.push(i as u8);}var b:u8[varint]=a;assert(b.len==128&&b[127]==127);print("varint_128");}
