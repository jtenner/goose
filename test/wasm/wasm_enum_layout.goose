struct Cell { n: i64 }
enum Packet { Data { lead: u8 = 7, pad, word: u32 = 305419896, pad 3, tail: i16 = -3, cell: Cell = Cell { n: 19 }, items: u16[..300], optional: i64? }, Off }
struct Holder { before: u8, packet: Packet, payload: Packet.Data, after: u16 }
fn main() {
 var p: Packet = Packet.Data { items: [4, 5] }; var c: Packet = copy(p); var d: Packet = default<Packet>();
 var v: Packet.Data = Packet.Data { items: [8] }; var w: Packet.Data = copy(v); w.cell.n = 77; assert(v.cell.n == 19);
 var holder: Holder = Holder { before: 9, packet: c, payload: v, after: 65000 };
 match holder.packet { Data b => { assert(b.lead == 7); assert(b.word == 305419896); assert(b.tail == -3); assert(b.cell.n == 19); assert(b.items.len == 2); assert(b.items[1] == 5); let optional: i64? = b.optional; assert(optional == null); var own: Packet.Data = copy(b); own.items[0] = 99; assert(b.items[0] == 4); }, Off => assert(false) }
 match d { Data b => { assert(b.items.len == 0); assert(b.lead == 7); assert(b.cell.n == 19); }, Off => assert(false) }
 var off: Packet = Packet.Off; match off { Data => assert(false), Off => print("layout") }
 assert(holder.before == 9); assert(holder.after == 65000); assert(holder.payload.items[0] == 8);
}
