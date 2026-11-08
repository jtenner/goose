recursive fn make()->u8[..0]{print("inside");return[];}fn main(){var b:u8[]=make();assert(b.len==0);print("zero_call_variable");}
