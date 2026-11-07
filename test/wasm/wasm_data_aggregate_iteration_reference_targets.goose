struct Link { marker: u8, target: i64& }
struct Maybe { target: i64? }
var global_value: i64 = 5;
fn main() {
    var plain: i64 = 10; var data: i64[] = [20];
    var rows: Link[] = [Link { marker: 1, target: plain },
                       Link { marker: 2, target: global_value },
                       Link { marker: 3, target: data[0] }];
    for row, i in rows {
        if i == 0 { rows[0].target .= data[0]; assert(row.target .== &plain); }
        if i == 1 { rows[1].target .= data[0]; assert(row.target .== &global_value); }
        row.target += 1;
    }
    assert(plain == 11); assert(global_value == 6); assert(data[0] == 21);
    var optional: Maybe[] = [Maybe { target: plain }, Maybe {}];
    for row, i in optional {
        var selected: i64? = row.target;
        if selected { assert(i == 0); selected += 2; } else { assert(i == 1); }
    }
    assert(plain == 13); print("targets=", plain, ",", global_value, ",", data[0]);
}
