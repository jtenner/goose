struct S{x:i64,y:i64}fn main(){var a=S{3,6};a*=a.x;assert(a.x==9&&a.y==18);a/=3;assert(a.x==3&&a.y==6);print("scalar");}
