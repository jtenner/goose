struct S{x:i16,y:i16}fn main(){var a:S[2]=[S{3,4},S{5,6}];var b:S[2]=[S{2,3},S{4,5}];a*=b;assert(a[0].x==6&&a[0].y==12&&a[1].x==20&&a[1].y==30);print("nested_rows");}
