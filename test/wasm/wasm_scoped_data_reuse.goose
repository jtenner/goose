fn main() {
    var sum = 0;
    for outer in 20 {
        var temporary: i64[>..] = [];
        for i in 9000 { temporary.push(i); }
        sum += temporary[8999];
    }
    print(sum);
}
