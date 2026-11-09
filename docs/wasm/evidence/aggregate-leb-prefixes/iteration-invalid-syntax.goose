struct S{n:i64}fn main(){var a:S[varint]=[S{7};128];var sum:i64=0;for copy row in a{sum+=row.n;}assert(sum==896);print("iteration");}
