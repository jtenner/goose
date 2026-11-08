var values:i64[2]=[7,8];recursive fn right()->i64[..3]{values[0]=9;return[9,8];}
fn main(){assert(values==right());assert(values[0]==9);print("view_mutation");}
