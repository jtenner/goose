var target:i64[2]=[1,2];recursive fn run()->i64{target=[9,{defer{print("inner");}return 7;8}];return 0;}fn main(){assert(run()==7);assert(target[0]==1);assert(target[1]==2);print("early_owner");}
