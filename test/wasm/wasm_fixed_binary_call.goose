recursive fn add(a:i64[2],b:i64[2])->i64[2]{return a+b;}fn main(){let c=add([7,-8],[3,4]);assert(c[0]==10&&c[1] == -4);print("call");}
