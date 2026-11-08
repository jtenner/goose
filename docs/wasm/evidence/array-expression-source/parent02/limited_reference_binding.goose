var source:u8[..3]=[7,8];fn main(){var r:u8[..3]& =({defer source[0]=99;source});var b:u8[]=copy(r);assert(b.len==2&&b[0]==99&&source[0]==99);print("reference_binding");}
