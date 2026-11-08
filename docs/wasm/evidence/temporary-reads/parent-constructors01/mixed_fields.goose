struct S{f:f32,d:f64,b:bool,link:i64&}
var calls:i64=0;recursive fn make(p:i64&)->S{calls++;return S{f:1.25,d:-0.0,b:true,link:p};}
recursive fn read(p:i64&)->i64{return p;}
fn main(){var data:i64[]=[7];assert(make(data[0]).f==1.25);assert(1.0/make(data[0]).d<0.0);assert(make(data[0]).b);assert(read(make(data[0]).link)==7);assert(calls==4);print("mixed_fields");}
