enum E{Empty,Value{n:i64}}struct H{tag:u8,empty:E.Empty}recursive fn make()->E.Empty{return E.Empty;}fn main(){let h=H{90,make()};assert(h.tag==90);print("enum_field");}
