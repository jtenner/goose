fn main(){var a:i64[600]=[7;600];var b:i64[600]=[3;600];a[599]=9;b[599]=5;a+=b;for i in 599{assert(a[i]==10);}assert(a[599]==14);print("large");}
