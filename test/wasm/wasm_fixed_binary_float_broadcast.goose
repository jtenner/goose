struct S{x:f32,y:f32}fn main(){var a=S{1.25,2.5};let b=a*2.0;let c=10.0/a;assert(b.x==2.5&&b.y==5.0);assert(c.x==8.0&&c.y==4.0);print("float_broadcast");}
