struct S{n:i64}
recursive fn run()->i64{var a:S[0]=[S{n:{defer{var bytes:u8[70000]=[7;70000];assert(bytes[69999]==7);}return 7;8}};0];return 0;}
fn main(){assert(run()==7);print("defer_exit");}
