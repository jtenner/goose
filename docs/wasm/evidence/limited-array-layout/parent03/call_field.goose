struct S{xs:u8[..3]}recursive fn make()->S{return S{[7,8]};}fn main(){var b:u8[..256]=make().xs;assert(b.len==2&&b[1]==8);print("call_field");}
