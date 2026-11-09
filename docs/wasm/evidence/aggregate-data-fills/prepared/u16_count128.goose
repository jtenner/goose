struct S{mark:u8,n:i64,tail:u16}fn main(){var rows:S[u16]=[S{7,-8,900};128];assert(rows.len==128);assert(rows[0].mark==7&&rows[127].n== -8&&rows[127].tail==900);print("u16_count128");}
