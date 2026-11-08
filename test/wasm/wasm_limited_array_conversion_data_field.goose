struct S{xs:u8[..3]}fn main(){var rows:S[]=[S{[7,8]}];var b:u8[]=rows[0].xs;assert(b.len==2&&b[1]==8);print("data_field");}
