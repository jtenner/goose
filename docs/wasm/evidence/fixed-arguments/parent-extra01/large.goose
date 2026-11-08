struct S{bytes:u8[70000],n:i64}
recursive fn read(p:S)->i64{p.bytes[69999]=11;return p.n+p.bytes[69999];}
fn main(){var s:S=S{bytes:default<u8[70000]>(),n:7};assert(read(s)==18);assert(s.bytes[69999]==0);print("large");}
