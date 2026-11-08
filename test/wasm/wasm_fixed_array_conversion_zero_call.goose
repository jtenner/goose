recursive fn make()->i64[0]{return default<i64[0]>();}fn main(){var c:i64[]=make();assert(c.len==0);print("zero_call");}
