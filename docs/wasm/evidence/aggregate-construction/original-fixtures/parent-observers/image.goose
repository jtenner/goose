struct Cell{tag:u8,n:u16}
struct H{left:u8,rows:Cell[..3],right:u16}
var before:u16=39030;
var holder:H=H{left:129,rows:[],right:58099};
var after:u32=878082192;
recursive fn value()->u16{print("eval");return 17767;}
fn main(){print("seed");holder=H{left:17,rows:[Cell{tag:34,n:value()};2],right:31355};print("filled");assert(holder.rows.len==2);assert(holder.rows[1].n==17767);assert(holder.left==17);assert(holder.right==31355);assert(before==39030);assert(after==878082192);}
