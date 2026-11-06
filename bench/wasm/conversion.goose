fn main() {
    var value = 0.25;
    var total: i64 = 0;
    for i in 200000 {
        total += value as! i64;
        value += 0.5;
    }
    print(total);
}
