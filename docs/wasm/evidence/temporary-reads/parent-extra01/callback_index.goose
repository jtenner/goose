recursive fn index()->i64{var scratch:i64[2]=[99,100];return scratch[0]-98;}
fn apply<F>(n:i64)->i64{F(n)[index()]}
fn main(){assert(apply(7){n=>[n,n+1]}==8);print("callback_index");}
