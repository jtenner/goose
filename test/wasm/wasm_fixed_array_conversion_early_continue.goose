fn main(){var a:i64[2]=[7,8];var i=0;while i<4{print("head");var c:i64[]=a*(if i<3{i++;continue;}else{2});print("after");assert(c[0]==14&&c[1]==16);i++;}print("early_continue");}
