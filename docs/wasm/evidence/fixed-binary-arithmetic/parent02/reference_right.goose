var source:i64[2]=[7,-8];recursive fn change()->i64[2]&{source[0]=10;return source;}fn main(){let c=source+change();assert(c[0]==17&&c[1] == -16);assert(source[0]==10);print("reference_right");}
