// error: const fn if scalar kind mismatch
const fn bad(x:u64)->u64{return if true {x} else {false};}
fn main(){}
