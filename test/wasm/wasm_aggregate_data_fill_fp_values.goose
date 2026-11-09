struct S{x:f32,y:f64,z:bool}fn main(){var a:S[u32]=[S{-1.25,3.5,true};3];assert(a[2].x== -1.25&&a[1].y==3.5&&a[0].z);print("fp_values");}
