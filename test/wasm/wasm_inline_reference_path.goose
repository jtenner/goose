fn main() {
    var a: i64[3] = [1, 2, 3];
    var b: i64[3] = [10, 20, 30];
    var owners: i64[3]&[1] = [a];
    for value in owners[0] {
        print(value);
        owners[0] .= b;
    }
}
