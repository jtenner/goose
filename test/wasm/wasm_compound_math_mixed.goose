struct S{x:i8,pad 1,y:u32,z:i64[2]}fn main(){var a=S{127,4294967295,[7,-8]};a+=S{1,2,[3,4]};assert(a.x == -128&&a.y==1&&a.z[0]==10&&a.z[1] == -4);print("mixed");}
