var a:i64[2]=[1,2];recursive fn inner()->i64{a=[3,4];return a[0];}
fn main(){a=[9,inner()];assert(a[0]==9);assert(a[1]==3);print("nested_replacement");}
