struct S{xs:u16[..3]}fn main(){var a:S[]=[S{[1,2,3]}];var r:u16& =a[0].xs[2];for i in 2{if i==0{a[0]=S{[1,2,3]};}else{a[0]=S{[]};}}print("slot=",r);assert(r==0);}
