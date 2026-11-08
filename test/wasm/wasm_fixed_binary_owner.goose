struct S{a:f32,pad 2,b:f64}
var left:S=S{1.25,45.125};var right:S=S{-2.5,-37.25};
recursive fn prepare(l:S&,r:S&){l.a=1.25;l.b=45.125;r.a = -2.5;r.b = -37.25;print("before");}
fn main(){prepare(left,right);var result:S=left+right;print("after=",result.a==result.a,",",result.b==result.b);}
