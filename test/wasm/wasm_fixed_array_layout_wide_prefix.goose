fn main(){var a:u8[255]=[3;255];var b:u8[256]=[4;256];var c:u8[..255]=a;var d:u8[..256]=b;assert(c.len==255&&d.len==256&&c[254]==3&&d[255]==4);print("wide_prefix");}
