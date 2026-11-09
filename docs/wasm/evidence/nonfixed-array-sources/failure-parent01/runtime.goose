fn main(){var a:u8[..]=[73;256];assert(a.len==256&&a[0]==73&&a[255]==73);print("before");var b:u8[u8]=copy(a);print("after");}
