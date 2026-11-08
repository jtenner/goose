var target:i64[2]=[1,2];fn main(){for i in 4{target=[{print("live");target[0]+1},target[1]];print("done");}assert(target[0]==5);print("loop");}
