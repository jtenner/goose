var a:i64[2]=[7,-8];var calls:i64=0;recursive fn rhs()->i64[2]{calls++;a[0]=99;return [3,4];}fn main(){a+=rhs();assert(a[0]==10&&a[1] == -4&&calls==1);print("effect");}
