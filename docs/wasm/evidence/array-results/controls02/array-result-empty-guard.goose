recursive fn make()->u8[0]{print("inside");return default<u8[0]>();}
fn main(){var a:u8[0]=make();print(a.len);}
