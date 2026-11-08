var source:u8[2]=[209,226];fn main(){var b:u8[]=({defer source[0]=99;print("inside");source});print("after");assert(b.len==2&&b[0]==209&&b[1]==226&&source[0]==99);}
