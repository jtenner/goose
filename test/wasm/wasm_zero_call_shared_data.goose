var anchor:i64[]=[10,20];recursive fn same(a:i64[0])->i64[0]{return a;}fn main(){var a:i64[0]=[];let b=same(a);assert(&a .!= &b&&anchor.len==2&&anchor[0]==10&&anchor[1]==20);print("shared_data");}
