const fn w2(n:u64)->u64 {return if n>1 {2} else {1};}
const fn w4(n:u64)->u64 {return if n>3 {2+w2(n>>2)} else {w2(n)};}
const fn w8(n:u64)->u64 {return if n>15 {4+w4(n>>4)} else {w4(n)};}
const fn w16(n:u64)->u64 {return if n>255 {8+w8(n>>8)} else {w8(n)};}
const fn w32(n:u64)->u64 {return if n>65535 {16+w16(n>>16)} else {w16(n)};}
const fn width64(n:u64)->u64 {return if n>4294967295 {32+w32(n>>32)} else {w32(n)};}

const fn needs_edges(edges:bool,paths:bool)->bool{return edges||paths;}
const NEED:bool=needs_edges(false,true);
const WIDTH_0:u64=width64(1);
const WIDTH_1:u64=width64(31);
const WIDTH_2:u64=width64(2047);
const WIDTHS:u8[3]=[WIDTH_0 as u8,WIDTH_1 as u8,WIDTH_2 as u8];
const RECORD_BYTES:u64=(WIDTH_0+WIDTH_1+WIDTH_2+7)/8;
struct Record {data:u8[RECORD_BYTES], const if NEED {tag:u8,} else {bad:missing::Type,}}
fn main(){
    let record=Record{data:[0;RECORD_BYTES],const if NEED {tag:7,} else {bad:missing(),}};
    print(WIDTHS[0]);print(WIDTHS[1]);print(WIDTHS[2]);
    print(record.data.len);print(record.tag);
}
