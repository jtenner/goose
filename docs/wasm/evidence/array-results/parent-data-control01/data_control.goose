struct H{lead:u8,items:u16[..4],tail:u16}
recursive fn choice(flag:bool)->bool{return flag;}
fn main(){var rows:H[]=[
 H{lead:90,items:{var scratch:u16[]=[4660];[scratch[0],22136]},tail:{print("row0");13124}},
 H{lead:91,items:if choice(true){var scratch:u16[]=[7];[scratch[0],8]}else{var scratch:u16[]=[99];[scratch[0],100]},tail:{print("row1");21862}},
 H{lead:92,items:if choice(false){var scratch:u16[]=[99];[scratch[0],100]}else{var scratch:u16[]=[11];[scratch[0],12]},tail:{print("row2");30600}}];
 assert(rows.len==3);assert(rows[0].lead==90);assert(rows[0].items.len==2);assert(rows[0].items[0]==4660);assert(rows[0].items[1]==22136);assert(rows[0].tail==13124);
 assert(rows[1].lead==91);assert(rows[1].items.len==2);assert(rows[1].items[0]==7);assert(rows[1].items[1]==8);assert(rows[1].tail==21862);
 assert(rows[2].lead==92);assert(rows[2].items.len==2);assert(rows[2].items[0]==11);assert(rows[2].items[1]==12);assert(rows[2].tail==30600);print("data_control");}
