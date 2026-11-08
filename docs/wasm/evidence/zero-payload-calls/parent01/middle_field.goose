struct H{left:i64,empty:i64[0],right:i64}recursive fn make()->i64[0]{var x:i64[0]=[];return x;}fn main(){let h=H{13,make(),17};assert(h.left==13&&h.right==17&&h.empty.len==0);print("middle_field");}
