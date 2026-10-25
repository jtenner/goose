// runtime-debug: fixed decimals must preserve exact integers and round the
// fractional part half up, including after decimal scaling.
import std;

fn fixed(v: f64, decimals: i64) {
    var out: u8[>..] = [];
    format_flt(out, v, decimals);
    print(out);
}

fn main() {
    // Adjacent exact integers around 2^52, where adding 0.5 can change an
    // odd integer, and the last odd integer below 2^53.
    var integers: f64[>..] = [4503599627370495.0, 4503599627370496.0,
                             4503599627370497.0, 4503599627370498.0,
                             4503599627370499.0, 9007199254740991.0];
    for v in integers {
        fixed(v, 0);
        fixed(-v, 0);
    }
    fixed(450359962737049.7, 1);
    fixed(-450359962737049.7, 1);
    fixed(45035996273704.97, 2);
    fixed(-45035996273704.97, 2);
    // Values just below a half must not become a half during rounding.
    var fractions: f64[>..] = [0.0, 0.49999999999999994, 0.5,
                              1.4999999999999998, 1.5, 2.5, 3.5, 9.5];
    for v in fractions {
        fixed(v, 0);
        fixed(-v, 0);
    }
    fixed(0.005, 2);
    fixed(-0.005, 2);
    fixed(9.875, 2);
    fixed(-9.875, 2);
}
