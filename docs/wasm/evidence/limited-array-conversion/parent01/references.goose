struct S{n:i64}fn main(){var rows:S[]=[S{7},S{8}];var a:S&[..3]=[rows[0],rows[1]];var b:S&[]=a;b[0].n=99;assert(rows[0].n==99&&b[1].n==8);print("references");}
