struct O{x:i64[2]} recursive fn make()->O{return O{[7,8]};} fn apply<F>()->i64{F(make().x)} fn main(){assert(apply(){p:i64[2]& =>p[0]+p[1]}==15);print("array_field");}
