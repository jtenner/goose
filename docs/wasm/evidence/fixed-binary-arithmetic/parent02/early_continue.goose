fn main(){var a:i64[2]=[7,8];var i=0;while i<4{print("head");let r:i64[2]=a*(if i<3{i++;continue;}else{2});assert(r[0]==14&&r[1]==16);i++;}print("early_continue");}
