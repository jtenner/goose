var global_value = 123.75;
var global_integer = global_value as! i64;
var global_single: f32 = 258.75;
var global_byte = global_single as! u8;
fn main() { print(global_integer, ",", global_byte); }
