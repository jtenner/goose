recursive fn mixed(a:f32[2],b:f64[2],c:bool[2],x:i64)->f64{assert(a[1]==2.0);assert(b[0]==1.5);assert(c[0]);assert(!c[1]);c[0]=false;return(a[0] as f64)+b[1]+(x as f64);}
fn main(){var a:f32[2]=[1.25,2.0];var b:f64[2]=[1.5,2.5];var c:bool[2]=[true,false];assert(mixed(a,b,c,3)==6.75);assert(c[0]);print("mixed");}
