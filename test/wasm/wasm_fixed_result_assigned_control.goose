struct S{n:i64}
var target:S=S{n:1};var yes:bool=true;
fn main(){target=if yes{S{n:target.n+1}}else{S{n:9}};assert(target.n==2);target={var old:i64=target.n;S{n:old+1}};assert(target.n==3);print("assigned_control");}
