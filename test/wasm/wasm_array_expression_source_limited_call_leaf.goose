recursive fn make()->u8[..3]{return[7,8];}fn main(){var b:u8[]=({make()});assert(b.len==2&&b[1]==8);print("limited_call_leaf");}
