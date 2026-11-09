struct O{x:i64[2]}recursive fn make()->O{return O{x:[7,8]};}recursive fn read(p:i64[2]&)->i64{return p[0]+p[1];}fn main(){assert(read(make().x)==15);print("array_field");}
