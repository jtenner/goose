recursive fn big()->i64{var a:u8[70000]=[7;70000];assert(a[69999]==7);return a[69999];}
struct S{n:i64=big()}
fn main(){var a:S[2]=default<S[2]>();assert(a[0].n==7);assert(a[1].n==7);print("default_growth");}
