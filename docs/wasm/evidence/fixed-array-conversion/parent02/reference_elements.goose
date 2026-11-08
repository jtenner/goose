fn main(){var x:i64=7;var y:i64=20;var a:i64&[2]=[x,x];var c:i64&[]=a;c[0].=y;assert(c[0]==20&&a[0]==7);c[1]=9;assert(x==9&&a[1]==9);print("reference_elements");}
