recursive fn make()->i64[2]{return[7,-8];}fn main(){var c:i64[..3]=[1,2,3];c=make();assert(c.len==2&&c[0]==7&&c[1] == -8);print("call");}
