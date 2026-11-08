var calls:i64=0;recursive fn make()->i64[2]{calls++;defer{calls+=10;}return[3,4];}
fn main(){make();assert(calls==11);print("discard");}
