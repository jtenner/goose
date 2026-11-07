enum E { Data { x: u32, y: u8, z: u16 }, Empty }
var original: E = E.Data { x: 305419896, y: 19, z: 65000 };
fn main() {
 match original {
  Data p => {
   assert(p.x == 305419896);
   assert(p.y == 19);
   assert(p.z == 65000);
   print("payload");
  },
  Empty => assert(false)
 }
}
