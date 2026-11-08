struct S{x:i8,pad 1,y:u32,z:i64[2]}fn main(){var a=S{127,4294967295,[7,-8]};var b=S{1,2,[3,4]};let c=a+b;assert(c.x == -128&&c.y==1);assert(c.z[0]==10&&c.z[1] == -4);print("mixed_int");}
