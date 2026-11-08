struct S{x:f32,pad 2,y:f64}fn main(){var a=S{1.25,45.125};a+=S{-2.5,-37.25};assert(a.x == -1.25&&a.y==7.875);a*=S{2.0,4.0};assert(a.x == -2.5&&a.y==31.5);print("float");}
