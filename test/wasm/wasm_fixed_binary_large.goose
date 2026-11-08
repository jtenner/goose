fn main(){var a:i64[600]=[7;600];var b:i64[600]=[3;600];a[599]=9;b[599]=5;let c=a+b;assert(c.len==600);for i in 599{assert(c[i]==10);}assert(c[599]==14);print("large");}
