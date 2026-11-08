var x:i64=7;var y:i64=9;var refs:i64&[2]=[&x,&x];
recursive fn change()->i64&[2]{refs[0].=y;return[&x,&x];}
fn main(){assert(refs==change());assert(refs[0] .== &y);print("ref_rebind");}
// warning: redundant &: x binds by reference here without it
// warning: redundant &: x binds by reference here without it
// warning: redundant &: x binds by reference here without it
// warning: redundant &: x binds by reference here without it
