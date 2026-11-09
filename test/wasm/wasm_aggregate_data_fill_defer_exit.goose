struct S{n:i64}recursive fn run()->i64{var a:S[u16]=[S{n:{defer{var bytes:u8[]=[7;70000];assert(bytes[69999]==7);}return 7;8}};0];return 0;}fn main(){assert(run()==7);print("defer_exit");}
