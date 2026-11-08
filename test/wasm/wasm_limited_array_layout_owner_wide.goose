fn main(){var a:u8[..256]=[];for i in 0..256 {a.push(i as u8);}print("before");var b:u8[..65536]=a;print("wide");var c:u8[..512]=b;print("after");assert(c.len==256&&c[255]==255);}
