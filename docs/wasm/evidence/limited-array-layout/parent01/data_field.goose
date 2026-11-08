struct B{xs:u8[..256]}fn main(){var a:u8[..3]=[7,8];var rows:B[]=[B{a}];rows[0].xs[0]=99;assert(rows[0].xs.len==2&&rows[0].xs[1]==8&&a[0]==7);print("data_field");}
