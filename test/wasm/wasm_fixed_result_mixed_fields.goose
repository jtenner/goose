struct S{f:f32,d:f64,b:bool,link:f64&}
recursive fn make(link:f64&)->S{return S{f:1.25,d:2.5,b:true,link:link};}
fn main(){var value:f64=7.0;var s:S=make(value);assert(s.f==1.25);assert(s.d==2.5);assert(s.b);s.link+=1.0;assert(value==8.0);print("mixed_fields");}
