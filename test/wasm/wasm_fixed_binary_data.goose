struct S{x:i64,y:i64}fn main(){var a=S{7,-8};var b=S{3,4};var rows:S[]=[a+b,a-b];assert(rows[0].x==10&&rows[0].y == -4);assert(rows[1].x==4&&rows[1].y == -12);print("data");}
