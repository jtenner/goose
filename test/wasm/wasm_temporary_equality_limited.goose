recursive fn make(n:i64)->u16[..4]{if n==0{return[];}if n==1{return[7];}return[7,8];}
fn main(){assert(make(0)==make(0));assert(make(1)!=make(2));assert(make(2)==make(2));print("limited");}
