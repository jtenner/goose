var values:i64[..4]=[7,8];recursive fn right()->i64[..3]{values.push(9);values[0]=9;return[9,8];}
fn main(){assert(values==right());assert(values.len==3);print("view_length");}
