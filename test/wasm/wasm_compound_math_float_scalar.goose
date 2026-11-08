struct S{x:f32,y:f32}fn main(){var a=S{1.25,2.5};a*=a.x;assert(a.x==1.5625&&a.y==3.125);a/=1.25;assert(a.x==1.25&&a.y==2.5);print("float_scalar");}
