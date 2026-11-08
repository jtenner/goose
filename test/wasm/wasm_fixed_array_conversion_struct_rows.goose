struct S{x:i64,y:i64&}fn main(){var x:i64=7;var a:S[2]=[S{1,x},S{2,x}];var c:S[]=a;c[0].x=99;c[1].y=9;assert(a[0].x==1&&x==9&&c[0].x==99);print("struct_rows");}
