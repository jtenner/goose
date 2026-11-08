struct B{xs:u8[..256]}fn main(){var a:u8[..3]=[7,8];var rows:B[]=[B{[1,2,3]}];rows[0].xs=a;assert(rows[0].xs.len==2&&rows[0].xs[0]==7&&rows[0].xs[1]==8);print("assign_field");}
