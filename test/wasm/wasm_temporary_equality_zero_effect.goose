var calls:i64=0;recursive fn make()->i64[2]{calls++;return[7,8];}
fn main(){var empty:i64[0]=default<i64[0]>();assert(!(empty==make()));assert(calls==1);print("zero_effect");}
