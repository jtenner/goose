struct S{n:i64}
recursive fn mixed(p:S,b:bool,x:f32,y:f64,out:f64&)->f64{assert(b);assert(p.n==7);out+=x+y;return out;}
recursive fn result32(p:S,x:f32)->f32{assert(p.n==7);return x;}
recursive fn flag(p:S,b:bool)->bool{return p.n==7&&b;}
fn main(){var s:S=S{n:7};var value:f64=0.25;assert(mixed(s,true,1.25,2.5,value)==4.0);assert(value==4.0);assert(result32(s,1.5)==1.5);assert(flag(s,true));assert(!flag(s,false));assert(s.n==7);print("mixed_scalars");}
