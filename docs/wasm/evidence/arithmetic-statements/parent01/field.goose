struct H{v:i64[2]}fn main(){var h=H{[7,-8]};h.v+=[3,4];assert(h.v[0]==10&&h.v[1] == -4);print("field");}
