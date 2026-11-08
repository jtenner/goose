var a:i64[2]=[1,2];recursive fn read_old()->i64{return a[0];}
fn main(){a=[9,read_old()];assert(a[0]==9);assert(a[1]==1);print("old_target");}
