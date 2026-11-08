var value:i64[2]=[3,4];var calls:i64=0;
recursive fn borrow()->i64[2]&{calls++;return value;}
fn main(){var copied:i64[2]=borrow();copied[0]=9;assert(value[0]==3);borrow();assert(calls==2);print("reference_control");}
