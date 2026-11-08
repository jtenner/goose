recursive fn make()->u8[2]{return[7,8];}fn main(){var b:u8[]=({make()});assert(b.len==2&&b[1]==8);print("fixed_call_leaf");}
