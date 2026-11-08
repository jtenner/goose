var source:i64[2]=[7,-8];
recursive fn later()->i64{source[0]=99;return 0;}
recursive fn transform(a:i64[2],b:i64)->i64[2]{if b!=0{a[0]+=b;}return -a;}
fn main(){var result:i64[2]=transform(-source,later());assert(result[0]==7);assert(result[1] == -8);assert(source[0]==99);print("array_call");}
