var source:u8[..3]=[7,8];fn main(){var b:u8[]=copy(({defer source[0]=99;&source}));assert(b.len==2&&b[0]==99&&source[0]==99);print("limited_reference_block");}
