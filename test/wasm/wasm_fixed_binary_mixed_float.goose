struct S{x:f32,pad 2,y:f64}fn main(){var a=S{1.5,-2.0};var b=S{0.5,2.0};let c=a+b;let d=a*b;assert(c.x==2.0&&c.y==0.0);assert(d.x==0.75&&d.y == -4.0);print("mixed_float");}
