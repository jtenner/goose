struct S{n:f32}recursive fn make()->S{return S{1.25};}recursive fn read(p:f32&)->f32{return p+0.5;}fn main(){assert(read(make().n)==1.75);print("f32");}
