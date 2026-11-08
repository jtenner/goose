var scalar:i64=3;recursive fn values()->i64[2]{scalar=99;return [3,6];}fn main(){let c=scalar*values();assert(c[0]==9&&c[1]==18);assert(scalar==99);print("left_scalar_effect");}
