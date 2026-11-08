var source:i64[2]=[7,-8];recursive fn change()->i64[2]{source[0]=99;return [3,4];}fn main(){let c=source+change();assert(c[0]==10&&c[1] == -4);assert(source[0]==99);print("left_effect");}
