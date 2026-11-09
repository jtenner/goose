struct S{n:f32} recursive fn make()->S{return S{1.25};} fn apply<F>()->f32{F(make().n)} fn main(){assert(apply(){p:f32& =>p+0.5}==1.75);print("f32");}
