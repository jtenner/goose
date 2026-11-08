struct S{a:f32,pad 2,b:f64}fn main(){var a:S[2]=[S{1.5,2.25},S{3.5,4.75}];var c:S[..3]=a;c[0].a=9.5;assert(c.len==2&&c[0].a==9.5&&a[0].a==1.5&&c[1].b==4.75);print("padded");}
