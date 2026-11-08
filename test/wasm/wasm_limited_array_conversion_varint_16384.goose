fn main(){var a:u8[..65536]=[];for i in 0..16384{a.push(i as u8);}var b:u8[varint]=a;assert(b.len==16384&&b[16383]==255);print("varint_16384");}
