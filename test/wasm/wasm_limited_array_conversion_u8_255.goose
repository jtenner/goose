fn main(){var a:u8[..256]=[];for i in 0..255{a.push(i as u8);}var b:u8[u8]=a;assert(b.len==255&&b[254]==254);print("u8_255");}
