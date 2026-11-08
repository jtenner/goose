fn apply<F>()->i64{F([3,4])}
fn main(){var n:i64=apply(){p=>p[0]+p[1]};assert(n==7);print("callback");}
