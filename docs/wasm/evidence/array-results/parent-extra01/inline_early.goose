var calls:i64=0;inline fn make(early:bool)->i64[2]{defer{calls++;}if early{return[3,4];}return[7,8];}
fn main(){var a:i64[2]=make(true);var b:i64[2]=make(false);assert(a[1]==4);assert(b[1]==8);assert(calls==2);print("inline_early");}
