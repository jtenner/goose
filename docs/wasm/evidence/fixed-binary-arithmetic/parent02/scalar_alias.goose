struct S{x:i64,y:i64}fn main(){var a:i64[2]=[3,6];a=a*a[0];assert(a[0]==9&&a[1]==18);var s=S{3,6};s=s.x*s;assert(s.x==9&&s.y==18);print("scalar_alias");}
