var values:i64[2]=[7,-8];recursive fn index()->i64{values[1]=99;return 1;}
fn main(){assert((-values)[index()]==8);assert(values[1]==99);print("index_effect");}
