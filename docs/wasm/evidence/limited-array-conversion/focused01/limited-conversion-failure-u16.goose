fn main(){var a:u8[..65536]=[];for i in 0..65536{a.push(i as u8);}print("before");var b:u8[u16]=a;print("after");}
