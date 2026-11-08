recursive fn change(a:u8[..256]&)->u8[..256]&{a.push(8);return a;}fn main(){var a:u8[..256]=[7];var b:u8[..3]=change(a);assert(b.len==2&&b[1]==8);print("source_effect");}
