struct S{bytes:u8[70000],n:i64}
recursive fn make(n:i64)->S{var saved:S=S{bytes:default<u8[70000]>(),n:n};saved.bytes[69999]=11;return saved;}
fn main(){var s:S=make(7);assert(s.n==7);assert(s.bytes[0]==0);assert(s.bytes[69999]==11);print("growth");}
