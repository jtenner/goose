enum E { Data { values: i64[2] }, Empty }
fn main() { var value: E = E.Data { values: [3, 4] }; var total: i64 = 0; match value { Data p => { for n in p.values { total += n; } }, Empty => assert(false) } assert(total == 7); print("variant-field"); }
