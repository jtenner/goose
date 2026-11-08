struct H{a:i64[2]}fn main(){var rows:H[]=[H{[7,-8]}];var c:i64[>..<]=rows[0].a;c[1]=99;assert(rows[0].a[1] == -8&&c[0]==7&&c[1]==99);print("field_data");}
