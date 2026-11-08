var source:u16[2]=[77,88];var trace:i64=0;
recursive fn left()->i64{trace=trace*10+1;return 0;}
recursive fn right(refs:u16[2]&[1]&,replacement:u16[2]&)->u16[2]&{refs[0] .= replacement;trace=trace*10+2;return source;}
fn main(){var a:u16[2]=[1,2];var b:u16[2]=[3,4];var refs:u16[2]&[1]=[a];refs[left()]=right(refs,b);assert(trace==12);assert(a[1]==88);assert(b[1]==4);assert(refs[0] .== &b);print("index_order");}
