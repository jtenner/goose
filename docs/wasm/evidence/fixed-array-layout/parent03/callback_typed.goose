fn apply<F>(a:i64[2])->i64{F(a)}fn main(){var a:i64[2]=[7,-8];assert(apply(a){p:i64[..3]=>p[0]+p[1]} == -1);print("callback_typed");}
