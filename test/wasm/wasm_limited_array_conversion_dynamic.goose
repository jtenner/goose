struct S{xs:u8[..3]}recursive fn take(a:S&){var b:u8[]=a.xs;assert(b.len==2&&b[1]==8);}fn main(){var a=S{[7,8]};take(a);var rows:S[]=[a];take(rows[0]);print("dynamic");}
