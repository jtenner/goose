recursive fn prepare(a:i64[2]&){a[0]=7;a[1] = -8;print("before");}fn main(){var a:i64[2]=[0,0];prepare(a);var c:i64[..3]=a;print("after");assert(c.len==2&&c[0]==7&&c[1] == -8);}
