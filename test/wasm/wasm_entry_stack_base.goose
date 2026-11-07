var seeded: i64 = {
    var temporary: i64[>..] = [1];
    main();
    temporary.push(9);
    temporary[1]
};
fn main() {
    var local: i64[>..] = [7];
    print(local[0]);
}
