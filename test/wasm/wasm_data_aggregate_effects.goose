var calls: i64 = 0;
recursive fn tick(value: i64) -> i64 { calls++; var scratch: i64[] = [value]; return scratch[0]; }
struct Row { before: u8, values: u16[..3], text: u8[3], zero: u32[2] = default<u32[2]>(), empty: i64[..1], after: u16 }
recursive fn exercise() -> i64 {
    var rows: Row[] = [Row { before: 1, values: [tick(7) as u16; 2], text: "abc", empty: [tick(11); 0], after: 60000 },
                      Row { before: 2, values: [tick(9) as u16; 3], text: "xyz", empty: [tick(13); 0], after: 65000 }];
    assert(rows[0].before == 1); assert(rows[1].before == 2);
    assert(rows[0].values.len == 2); assert(rows[0].values[1] == 7);
    assert(rows[1].values.len == 3); assert(rows[1].values[2] == 9);
    assert(rows[0].text[0] == 97); assert(rows[1].text[2] == 122);
    assert(rows[0].zero[0] == 0); assert(rows[1].zero[1] == 0);
    assert(rows[0].empty.len == 0); assert(rows[1].empty.len == 0);
    rows[0].zero[0] = 12345; rows[1].zero[1] = 54321;
    var copied: Row[] = copy(rows); copied[0].values[0] = 99;
    assert(rows[0].values[0] == 7); assert(copied[0].zero[0] == 12345);
    assert(copied[0].after == 60000); assert(copied[1].after == 65000);
    return rows[0].values[1] + rows[1].values[2];
}
fn main() {
    assert(exercise() == 16); assert(calls == 4);
    var keep: i64[] = [91];
    assert(exercise() == 16); assert(calls == 8); assert(keep[0] == 91);
    assert(exercise() == 16); assert(calls == 12);
    print("data-effects=ok");
}
