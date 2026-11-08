fn apply<F>(a:u8[..3])->i64{F(a)}fn main(){var a:u8[..3]=[7,8];assert(apply(a){p:u8[..256]=>p.len+p[1]}==10);print("callback_parameter");}
