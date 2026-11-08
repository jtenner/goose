recursive fn make()->i64[..3]{return[7,-8];}fn main(){var b:i64[u8]=make();assert(b.len==2&&b[0]==7&&b[1]== -8);print("u8_call");}
