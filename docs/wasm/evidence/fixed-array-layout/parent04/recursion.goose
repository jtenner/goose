recursive fn build(n:i64)->i64[2]{if n>0{var c:i64[..3]=build(n-1);return[c[0]+1,c[1]-1];}return[0,0];}fn main(){var c:i64[..3]=build(4);assert(c.len==2&&c[0]==4&&c[1] == -4);print("recursion");}
