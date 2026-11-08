recursive fn make()->u8[70000]{var a:u8[70000]=default<u8[70000]>();a[69999]=11;return a;}
fn main(){var a:u8[70000]=make();assert(a[0]==0);assert(a[69999]==11);print("growth");}
