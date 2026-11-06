fn main() {
    var state: u64 = 1234567;
    for i in 2000000 {
        state = (state * 6364136223846793005 + 1) ^ (state >> 17);
    }
    print(state);
}
