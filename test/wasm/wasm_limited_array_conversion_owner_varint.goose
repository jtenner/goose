fn main(){var a:u8[..256]=[];for i in 0..128{a.push(i as u8);}print("before");var b:u8[varint]=a;print("after");assert(b.len==128&&b[127]==127);}
