struct H{values:i64[..3]}recursive fn make()->i64[2]{return[7,-8];}fn main(){var h=H{make()};assert(h.values.len==2&&h.values[1] == -8);print("field_call");}
