fn main(){var a:u16[..3]=[1,2,3];var r:u16& =a[2];for i in 2{if i==0{a=[1,2,3];}else{a=[4];}}print("slot=",r);assert(r==0);}
