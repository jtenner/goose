fn leave(early: bool) -> i64 {
    var growing: i64[>..] = [10];
    var first: i64[2] = [1, 2]; var second: i64[2] = [3, 4];
    var selected: i64[2]& = first;
    defer {
        selected .= second;
        print("outer=", selected[1], ",", growing[0]);
        var scratch: u8[..2] = [7]; print("scratch=", scratch[0]);
    }
    {
        var other: i64[>..] = [20];
        defer { print("inner=", selected[0], ",", other[0]); }
        if early { return selected[0] + growing[0]; }
    }
    return selected[1] + growing[0];
}
fn main() {
    print("early=", leave(true));
    var live: i64[>..] = [90];
    print("normal=", leave(false)); print("live=", live[0]);
}
