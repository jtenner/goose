fn main(){var a:u8[..256];for(i in 0..256){a.push(i as u8);}var b:u8[..512]=a;assert(b.len==256&&b[255]==255);print("wide16");}
