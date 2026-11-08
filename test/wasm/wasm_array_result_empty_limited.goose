recursive fn make()->u8[..0]{return default<u8[..0]>();}
fn main(){var a:u8[..0]=make();assert(a.len==0);print("empty_limited");}
