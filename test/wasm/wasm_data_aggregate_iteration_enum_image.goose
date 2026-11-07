enum E { Data { n: i64 }, Other { b: u8[3] }, Empty }
fn main() {
 var rows: E[] = [E.Data { n: 7 }, E.Other { b: [1, 2, 3] }, E.Empty];
 print("seed");
 for e, i in rows { assert(&e .!= &rows[i]); print("enumcopy"); }
}
