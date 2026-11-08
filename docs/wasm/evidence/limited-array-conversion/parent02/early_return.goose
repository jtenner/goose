recursive fn use(a:u8[..3]&)->i64{var b:u8[]=a;return b[1];}fn main(){var a:u8[..3]=[7,8];assert(use(a)==8);var sibling:u8[]=[99];assert(use(a)==8&&sibling[0]==99);print("early_return");}
