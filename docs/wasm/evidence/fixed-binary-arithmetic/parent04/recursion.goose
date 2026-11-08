recursive fn build(n:i64)->i64[2]{if n==0{return [1,2];}return build(n-1)+[1,2];}fn main(){let c=build(4);assert(c[0]==5&&c[1]==10);print("recursion");}
