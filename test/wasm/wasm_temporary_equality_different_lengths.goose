var calls:i64=0;recursive fn two()->i64[2]{calls++;return[7,8];}
recursive fn three()->i64[3]{calls++;return[7,8,9];}
fn main(){assert(two()!=three());assert(calls==2);print("different_lengths");}
