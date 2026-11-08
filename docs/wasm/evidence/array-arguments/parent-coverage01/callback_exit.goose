var value:i64[2]=[3,4];recursive fn run<F>(early:bool)->i64{F(copy(value),{if early{return 7;}3})}
fn main(){assert(run(true){a,n=>a[0]+n}==7);assert(run(false){a,n=>a[0]+n}==6);assert(value[0]==3);print("callback_exit");}
