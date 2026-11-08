struct S{a:f32,pad 2,b:f64}fn main(){var a:S[..3]=[S{1.5,-2.0},S{3.5,4.0}];print("before");var b:S[..5]=a;print("after");assert(b.len==2&&b[1].a==3.5);}
