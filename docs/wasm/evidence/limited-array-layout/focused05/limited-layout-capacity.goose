var calls:i64=0;var target:u8[..3]=[1,2,3];
recursive fn make()->u8[..256]{calls++;target[2]=99;print("rhs");return[7,8,9,10];}
fn main(){print("before");target=make();print("after");}
