var source:i64[2]=[7,-8];var calls:i64=0;recursive fn change()->i64[2]{calls++;source[0]=99;return [3,4];}fn main(){source+change();assert(calls==1&&source[0]==99);print("discard");}
