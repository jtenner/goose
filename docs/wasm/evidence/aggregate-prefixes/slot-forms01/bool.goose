struct S{xs:bool[..3]}fn main(){var a:S[]=[S{[true,true,true]}];var r:bool& =a[0].xs[2];for i in 2{if i==0{a[0]=S{[true,true,true]};}else{a[0]=S{[false]};}}print("slot=",r);assert(!r);}
