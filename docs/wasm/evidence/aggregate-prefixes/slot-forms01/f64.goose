struct S{xs:f64[..3]}fn main(){var a:S[]=[S{[1.0,2.0,3.0]}];var r:f64& =a[0].xs[2];for i in 2{if i==0{a[0]=S{[1.0,2.0,3.0]};}else{a[0]=S{[4.0]};}}print("slot=",r);assert(r==0.0);}
