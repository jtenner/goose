struct S{mark:u8,values:u16[..3]}
recursive fn read(p:S)->i64{p.values[0]=9;return p.mark+p.values[0]+p.values.len;}
fn main(){var s:S=S{mark:7,values:[1,2]};assert(read(s)==18);assert(s.values[0]==1);assert(s.values.len==2);print("nested_array");}
