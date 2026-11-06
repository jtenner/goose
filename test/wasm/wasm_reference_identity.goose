fn main() {
    var a = 1.5;
    var b = 2.5;
    let p = &a;
    let q = &b;
    print(p .== q, ",", p .!= q, ",", p .== p);
    let optional_float: f64? = a;
    let missing_float: f64? = null;
    print(optional_float != null, ",", null != optional_float);
    print(missing_float == null, ",", null == missing_float);
    var bit = false;
    let optional_bool: bool? = bit;
    if optional_bool {
        print(optional_bool != null, ",", null != optional_bool);
    }
    var integer = 0;
    let optional_int: i64? = integer;
    if optional_int { print(optional_int != null, ",", null != optional_int); }
    let missing_int: i64? = null;
    print(missing_int == null, ",", null == missing_int);
    print(null .== null, ",", null .!= null);
}
