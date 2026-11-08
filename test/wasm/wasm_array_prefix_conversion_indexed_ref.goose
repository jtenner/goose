fn main(){var a:u8[u8]=[1,2,3];var refs:u8[u8]&[1]=[a];var b:u8[u16]=copy(refs[0]);assert(b.len==3&&b[0]==1&&b[2]==3);a[0]=9;assert(b[0]==1);print("indexed_ref");}
