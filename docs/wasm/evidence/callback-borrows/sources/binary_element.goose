fn apply<F>(a:i64[2],b:i64[2])->i64{F((a+b)[1])} fn main(){assert(apply([1,2],[3,4]){p:i64& =>p}==6);print("binary_element");}
