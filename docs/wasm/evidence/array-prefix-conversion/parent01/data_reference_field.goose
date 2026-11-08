struct H{r:u8[u8]&}fn main(){var a:u8[u8]=[1,2,3];var rows:H[]=[H{a}];var b:u8[u16]=copy(rows[0].r);assert(b.len==3&&b[0]==1&&b[2]==3);print("data_reference_field");}
