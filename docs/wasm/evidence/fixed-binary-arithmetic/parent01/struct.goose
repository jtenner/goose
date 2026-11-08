struct S{x:i16,y:i64,pad 2,z:i16[2]}fn main(){var a=S{1,2,[3,4]};var b=S{5,6,[7,8]};let c=a+b;assert(c.x==6&&c.y==8);assert(c.z[0]==10&&c.z[1]==12);print("struct");}
