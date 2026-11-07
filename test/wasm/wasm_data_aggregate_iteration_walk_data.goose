struct S { n: i64 }
var calls: i64 = 0;
recursive fn choose(a: S[]&[>..]&, last: S[]&) -> i64 { calls++; a.push(last); return 0; }
fn main() {
 var first: S[] = [S { n: 1 }, S { n: 2 }]; var second: S[] = [S { n: 10 }, S { n: 20 }]; var third: S[] = [S { n: 30 }, S { n: 40 }];
 var live: i64[] = [91]; var owners: S[]&[>..] = [first, second]; var total: i64 = 0;
 for row, i in owners[choose(owners, third)] { if i == 0 { owners[0] .= second; first[0].n += 100; assert(row.n == 1); } total += row.n; }
 assert(total == 21); assert(owners.len == 3); assert(calls == 1); assert(live[0] == 91);
 print("walk=", total, ",", calls);
}
