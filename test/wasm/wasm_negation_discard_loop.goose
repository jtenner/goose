var calls:i64=0;recursive fn make()->i64[2]{calls++;return[7,-8];}fn main(){for i in 4{print("head");-make();}assert(calls==4);print("negation_loop");}
