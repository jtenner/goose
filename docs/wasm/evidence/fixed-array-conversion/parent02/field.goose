struct H{a:i64[2]}fn main(){var h=H{[7,-8]};var c:i64[]=h.a;c[1]=99;assert(h.a[1] == -8&&c[0]==7&&c[1]==99);print("field");}
