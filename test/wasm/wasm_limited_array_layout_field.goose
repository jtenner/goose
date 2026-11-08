struct A{xs:u8[..3]}struct B{xs:u8[..256]}fn main(){var a=A{[7,8]};var b=B{a.xs};b.xs[0]=99;assert(b.xs.len==2&&b.xs[0]==99&&a.xs[0]==7);print("field");}
