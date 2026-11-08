recursive fn probe(yes:bool){var a:u8[2]=[7,8];var c:u8[3]=[9,10,11];var b:u8[]=if yes{a}else{c};assert(b.len==(if yes{2}else{3}));}fn main(){probe(true);probe(false);print("mixed");}
