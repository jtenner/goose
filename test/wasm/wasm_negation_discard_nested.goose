var calls:i64=0;recursive fn make()->i64[2]{calls++;return [7,-8];}fn main(){-(make()+make());assert(calls==2);print("nested");}
