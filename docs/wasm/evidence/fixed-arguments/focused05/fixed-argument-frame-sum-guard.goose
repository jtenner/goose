struct Huge{bytes:u8[2147483648]}
recursive fn take(a:Huge,b:Huge)->i64{return a.bytes[0]+b.bytes[0];}
fn main(){var x:Huge=default<Huge>();print(take(x,x));}
