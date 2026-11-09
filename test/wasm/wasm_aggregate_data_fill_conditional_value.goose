struct S{n:i64}fn main(){var flag:bool=true;var a:S[u16]=[if flag{S{7}}else{S{9}};2];assert(a[0].n==7&&a[1].n==7);print("conditional_value");}
