struct S{n:i64}
var yes:bool=true;fn main(){var s:S=if yes{S{n:7}}else{S{n:9}};assert(s.n==7);var b:S={var original:S=S{n:8};original};assert(b.n==8);print("declared_control");}
