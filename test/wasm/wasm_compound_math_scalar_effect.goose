var a:i64[2]=[7,-8];var calls:i64=0;recursive fn rhs()->i64{calls++;a[0]=99;return 2;}fn main(){a*=rhs();assert(a[0]==14&&a[1] == -16&&calls==1);print("scalar_effect");}
