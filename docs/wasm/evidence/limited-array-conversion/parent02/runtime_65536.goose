fn main(){var a:u8[..65536]=[];for i in 0..65536{a.push(i as u8);}var b:u8[..]=a;assert(b.len==65536&&b.cap==65536&&b[65535]==255);print("runtime65536");}
