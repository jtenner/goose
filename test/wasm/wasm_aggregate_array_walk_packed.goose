struct S { n: i64 }
var indexcalls: i64 = 0; var arraycalls: i64 = 0; var elementcalls: i64 = 0;
recursive fn choose(a: S[2]&[>..]&, last: S[2]&) -> i64 { indexcalls++; a.push(last); return 0; }
recursive fn arrayref(a: S[2]&) -> S[2]& { arraycalls++; return a; }
recursive fn elementref(a: S[2]&) -> S& { elementcalls++; return a[1]; }
fn main() {
 var first: S[2] = [S { n: 1 }, S { n: 2 }]; var second: S[2] = [S { n: 10 }, S { n: 20 }]; var third: S[2] = [S { n: 30 }, S { n: 40 }];
 var live: i64[] = [91]; var owners: S[2]&[>..] = [first, second];
 for &row, i in owners[choose(owners, third)] { if i == 0 { owners[0] .= second; } row.n += 1; }
 assert(owners.len == 3); assert(live[0] == 91); assert(indexcalls == 1); assert(first[0].n == 2); assert(first[1].n == 2); assert(second[0].n == 10); assert(second[1].n == 21);
 var current: S[2]& = first; for &row, i in current { if i == 0 { current .= third; } row.n += 2; }
 assert(first[0].n == 4); assert(first[1].n == 2); assert(third[0].n == 30); assert(third[1].n == 42);
 var saved: S[2] = copy(arrayref(first)); saved[0].n += 100; assert(first[0].n == 4); assert(saved[0].n == 104); assert(arraycalls == 1);
 var own: S = copy(elementref(saved)); own.n += 1000; assert(own.n == 1002); assert(saved[1].n == 2); assert(elementcalls == 1);
 var indexed: S[2] = copy(owners[0]); indexed[0].n += 100; assert(second[0].n == 10); assert(indexed[1].n == 21);
 print("walk=", first[0].n, ",", second[1].n, ",", third[1].n, ",", saved[0].n, ",", indexed[1].n, ",", indexcalls, ",", arraycalls, ",", elementcalls);
}
