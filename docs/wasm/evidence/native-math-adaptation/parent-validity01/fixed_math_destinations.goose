// runtime-debug: arithmetic uses operand shape before destination adaptation.
fn case_neg_0() {
    var a:i64[2]=[7,-8];
    var b:i64[..2]=-a;
    assert(b.len==2);
    assert(b[0]==-7);
    assert(b[1]==8);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("neg_0");
}

fn case_neg_1() {
    var a:i64[2]=[7,-8];
    var b:i64[..3]=-a;
    assert(b.len==2);
    assert(b[0]==-7);
    assert(b[1]==8);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("neg_1");
}

fn case_neg_2() {
    var a:i64[2]=[7,-8];
    var b:i64[]=-a;
    assert(b.len==2);
    assert(b[0]==-7);
    assert(b[1]==8);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("neg_2");
}

fn case_neg_3() {
    var a:i64[2]=[7,-8];
    var b:i64[>..]=-a;
    assert(b.len==2);
    assert(b[0]==-7);
    assert(b[1]==8);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("neg_3");
}

fn case_add_0() {
    var a:i64[2]=[7,-8];
    var b:i64[..2]=a+a;
    assert(b.len==2);
    assert(b[0]==14);
    assert(b[1]==-16);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("add_0");
}

fn case_add_1() {
    var a:i64[2]=[7,-8];
    var b:i64[..3]=a+a;
    assert(b.len==2);
    assert(b[0]==14);
    assert(b[1]==-16);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("add_1");
}

fn case_add_2() {
    var a:i64[2]=[7,-8];
    var b:i64[]=a+a;
    assert(b.len==2);
    assert(b[0]==14);
    assert(b[1]==-16);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("add_2");
}

fn case_add_3() {
    var a:i64[2]=[7,-8];
    var b:i64[>..]=a+a;
    assert(b.len==2);
    assert(b[0]==14);
    assert(b[1]==-16);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("add_3");
}

fn case_sub_0() {
    var a:i64[2]=[7,-8];
    var b:i64[..2]=a-a;
    assert(b.len==2);
    assert(b[0]==0);
    assert(b[1]==0);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("sub_0");
}

fn case_sub_1() {
    var a:i64[2]=[7,-8];
    var b:i64[..3]=a-a;
    assert(b.len==2);
    assert(b[0]==0);
    assert(b[1]==0);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("sub_1");
}

fn case_sub_2() {
    var a:i64[2]=[7,-8];
    var b:i64[]=a-a;
    assert(b.len==2);
    assert(b[0]==0);
    assert(b[1]==0);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("sub_2");
}

fn case_sub_3() {
    var a:i64[2]=[7,-8];
    var b:i64[>..]=a-a;
    assert(b.len==2);
    assert(b[0]==0);
    assert(b[1]==0);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("sub_3");
}

fn case_mul_0() {
    var a:i64[2]=[7,-8];
    var b:i64[..2]=a*a;
    assert(b.len==2);
    assert(b[0]==49);
    assert(b[1]==64);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("mul_0");
}

fn case_mul_1() {
    var a:i64[2]=[7,-8];
    var b:i64[..3]=a*a;
    assert(b.len==2);
    assert(b[0]==49);
    assert(b[1]==64);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("mul_1");
}

fn case_mul_2() {
    var a:i64[2]=[7,-8];
    var b:i64[]=a*a;
    assert(b.len==2);
    assert(b[0]==49);
    assert(b[1]==64);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("mul_2");
}

fn case_mul_3() {
    var a:i64[2]=[7,-8];
    var b:i64[>..]=a*a;
    assert(b.len==2);
    assert(b[0]==49);
    assert(b[1]==64);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("mul_3");
}

fn case_div_0() {
    var a:i64[2]=[7,-8];
    var b:i64[..2]=a/a;
    assert(b.len==2);
    assert(b[0]==1);
    assert(b[1]==1);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("div_0");
}

fn case_div_1() {
    var a:i64[2]=[7,-8];
    var b:i64[..3]=a/a;
    assert(b.len==2);
    assert(b[0]==1);
    assert(b[1]==1);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("div_1");
}

fn case_div_2() {
    var a:i64[2]=[7,-8];
    var b:i64[]=a/a;
    assert(b.len==2);
    assert(b[0]==1);
    assert(b[1]==1);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("div_2");
}

fn case_div_3() {
    var a:i64[2]=[7,-8];
    var b:i64[>..]=a/a;
    assert(b.len==2);
    assert(b[0]==1);
    assert(b[1]==1);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("div_3");
}

fn case_mod_0() {
    var a:i64[2]=[7,-8];
    var b:i64[..2]=a%a;
    assert(b.len==2);
    assert(b[0]==0);
    assert(b[1]==0);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("mod_0");
}

fn case_mod_1() {
    var a:i64[2]=[7,-8];
    var b:i64[..3]=a%a;
    assert(b.len==2);
    assert(b[0]==0);
    assert(b[1]==0);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("mod_1");
}

fn case_mod_2() {
    var a:i64[2]=[7,-8];
    var b:i64[]=a%a;
    assert(b.len==2);
    assert(b[0]==0);
    assert(b[1]==0);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("mod_2");
}

fn case_mod_3() {
    var a:i64[2]=[7,-8];
    var b:i64[>..]=a%a;
    assert(b.len==2);
    assert(b[0]==0);
    assert(b[1]==0);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("mod_3");
}

fn case_left_0() {
    var a:i64[2]=[7,-8];
    var b:i64[..2]=2*a;
    assert(b.len==2);
    assert(b[0]==14);
    assert(b[1]==-16);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("left_0");
}

fn case_left_1() {
    var a:i64[2]=[7,-8];
    var b:i64[..3]=2*a;
    assert(b.len==2);
    assert(b[0]==14);
    assert(b[1]==-16);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("left_1");
}

fn case_left_2() {
    var a:i64[2]=[7,-8];
    var b:i64[]=2*a;
    assert(b.len==2);
    assert(b[0]==14);
    assert(b[1]==-16);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("left_2");
}

fn case_left_3() {
    var a:i64[2]=[7,-8];
    var b:i64[>..]=2*a;
    assert(b.len==2);
    assert(b[0]==14);
    assert(b[1]==-16);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("left_3");
}

fn case_right_0() {
    var a:i64[2]=[7,-8];
    var b:i64[..2]=a*2;
    assert(b.len==2);
    assert(b[0]==14);
    assert(b[1]==-16);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("right_0");
}

fn case_right_1() {
    var a:i64[2]=[7,-8];
    var b:i64[..3]=a*2;
    assert(b.len==2);
    assert(b[0]==14);
    assert(b[1]==-16);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("right_1");
}

fn case_right_2() {
    var a:i64[2]=[7,-8];
    var b:i64[]=a*2;
    assert(b.len==2);
    assert(b[0]==14);
    assert(b[1]==-16);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("right_2");
}

fn case_right_3() {
    var a:i64[2]=[7,-8];
    var b:i64[>..]=a*2;
    assert(b.len==2);
    assert(b[0]==14);
    assert(b[1]==-16);
    assert(a[0]==7);
    assert(a[1] == -8);
    print("right_3");
}

fn case_neg_assign() {
    var a:i64[2]=[7,-8];
    var b:i64[..3]=[1,2,3];
    b=-a;
    assert(b.len==2);
    assert(b[0]==-7);
    assert(b[1]==8);
    print("neg_assign");
}

fn result_neg_return(a:i64[2])->i64[..3]{return -a;
}fn case_neg_return() {
    var a:i64[2]=[7,-8];
    let b=result_neg_return(a);
    assert(b.len==2);
    assert(b[0]==-7);
    assert(b[1]==8);
    print("neg_return");
}

fn consume_neg_argument(b:i64[..3]){assert(b.len==2);
    assert(b[0]==-7);
    assert(b[1]==8);
}fn case_neg_argument() {
    var a:i64[2]=[7,-8];
    consume_neg_argument(-a);
    print("neg_argument");
}

struct Box_neg_nested{b:i64[..3]}fn case_neg_nested() {
    var a:i64[2]=[7,-8];
    let box=Box_neg_nested{b:-a};
    let b=box.b;
    assert(b.len==2);
    assert(b[0]==-7);
    assert(b[1]==8);
    print("neg_nested");
}

fn case_neg_array() {
    var a:i64[2]=[7,-8];
    let boxes:i64[..3][1]=[-a];
    let b=boxes[0];
    assert(b.len==2);
    assert(b[0]==-7);
    assert(b[1]==8);
    print("neg_array");
}

fn case_add_assign() {
    var a:i64[2]=[7,-8];
    var b:i64[..3]=[1,2,3];
    b=a+a;
    assert(b.len==2);
    assert(b[0]==14);
    assert(b[1]==-16);
    print("add_assign");
}

fn result_add_return(a:i64[2])->i64[..3]{return a+a;
}fn case_add_return() {
    var a:i64[2]=[7,-8];
    let b=result_add_return(a);
    assert(b.len==2);
    assert(b[0]==14);
    assert(b[1]==-16);
    print("add_return");
}

fn consume_add_argument(b:i64[..3]){assert(b.len==2);
    assert(b[0]==14);
    assert(b[1]==-16);
}fn case_add_argument() {
    var a:i64[2]=[7,-8];
    consume_add_argument(a+a);
    print("add_argument");
}

struct Box_add_nested{b:i64[..3]}fn case_add_nested() {
    var a:i64[2]=[7,-8];
    let box=Box_add_nested{b:a+a};
    let b=box.b;
    assert(b.len==2);
    assert(b[0]==14);
    assert(b[1]==-16);
    print("add_nested");
}

fn case_add_array() {
    var a:i64[2]=[7,-8];
    let boxes:i64[..3][1]=[a+a];
    let b=boxes[0];
    assert(b.len==2);
    assert(b[0]==14);
    assert(b[1]==-16);
    print("add_array");
}

fn case_alias() {
    var a:i64[2]=[7,-8];
    a=-a;
    assert(a[0] == -7);
    assert(a[1]==8);
    a=a*a;
    assert(a[0]==49);
    assert(a[1]==64);
    print("alias");
}

fn case_float() {
    var a:f64[2]=[1.25,-2.5];
    var b:f64[..4]=-a;
    assert(b.len==2);
    assert(b[0] == -1.25);
    assert(b[1]==2.5);
    var c:f64[..4]=a+a;
    assert(c.len==2);
    assert(c[0]==2.5);
    assert(c[1] == -5.0);
    print("float");
}

fn main() {
    case_neg_0();
    case_neg_1();
    case_neg_2();
    case_neg_3();
    case_add_0();
    case_add_1();
    case_add_2();
    case_add_3();
    case_sub_0();
    case_sub_1();
    case_sub_2();
    case_sub_3();
    case_mul_0();
    case_mul_1();
    case_mul_2();
    case_mul_3();
    case_div_0();
    case_div_1();
    case_div_2();
    case_div_3();
    case_mod_0();
    case_mod_1();
    case_mod_2();
    case_mod_3();
    case_left_0();
    case_left_1();
    case_left_2();
    case_left_3();
    case_right_0();
    case_right_1();
    case_right_2();
    case_right_3();
    case_neg_assign();
    case_neg_return();
    case_neg_argument();
    case_neg_nested();
    case_neg_array();
    case_add_assign();
    case_add_return();
    case_add_argument();
    case_add_nested();
    case_add_array();
    case_alias();
    case_float();
}
