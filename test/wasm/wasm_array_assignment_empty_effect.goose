var source:u8[0]=[];var calls:i64=0;
recursive fn get()->u8[0]&{calls++;return source;}
fn main(){var target:u8[0]=[];target=get();assert(calls==1);assert(&target .!= &source);print("empty_effect");}
