recursive fn source(a:u8[..3]&)->u8[..3]&{a.push(8);return a;}fn main(){var a:u8[..3]=[7];var b:u8[]=source(a);assert(b.len==2&&b[1]==8);print("effects");}
