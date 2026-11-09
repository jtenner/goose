struct S{mark:u8,n:i64,tail:u16}fn main(){var rows:S[u32]=[S{7,-8,900};3];assert(rows.len==3);assert(rows[0].mark==7&&rows[2].n== -8&&rows[2].tail==900);print("u32_count3");}
