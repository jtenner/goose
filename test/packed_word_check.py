import subprocess,tempfile,pathlib
cases=[
('packed word W:u8 {a:u2,_:u6} fn main(){var w=W{a:1}; w.a=2;}',None),
('packed word W:u8 {a:u6,b:u3} fn main(){}','uses 9 bits'),
('packed word W:u8 {a:u2,a:bool} fn main(){}','duplicate field'),
('packed word W:u8 {a:u0} fn main(){}','between 1 and 128'),
('packed word W:u8 {a:u129} fn main(){}','between 1 and 128'),
('packed word W:u8 {a:i3} fn main(){}','signed packed'),
('packed word W:u8 {a:u2} fn main(){var w=W{a:4};}','does not fit packed word'),
('packed word W:u8 {a:u2} fn main(){let w=W{a:1}; w.a=2;}','let'),
('packed word W:u8 {a:u2} fn main(){var w=W{a:1}; let r=&w.a;}','not addressable'),
('packed word W:u8 {a:u2} fn f(x:u8&){} fn main(){var w=W{a:1}; f(w.a);}','not addressable'),
('packed word W:u8 {const if false {a:u129} else {a:u2},_:u6} fn main(){var w=W{a:1};}',None),
('packed word W:u128 {_:u60,a:u12,_:u56} fn main(){var w=W{a:4095};}',None),
('enum E{A,B,C} packed word W:u8 {e:E,_:u6} fn main(){var w=W{e:E.B};}',None),
('enum E{A{x:u8}} packed word W:u8 {e:E} fn main(){}','payload-free'),
('packed word W:u8 {a:u2} fn main(){var w=W{a:1}; let r=w as u8; let v=r as W;}',None),
('packed word W:u8 {a:u2} fn main(){var w=W{a:1}; let r=w as u64;}','exact backing'),
]
with tempfile.TemporaryDirectory(prefix='packed-check-') as td:
 for i,(source,expected) in enumerate(cases):
  p=pathlib.Path(td)/f'{i}.goose';p.write_text(source)
  r=subprocess.run(['goose++','--check',str(p)],capture_output=True,text=True)
  assert (r.returncode==0)==(expected is None) and (expected is None or expected in r.stderr+r.stdout),(i,r.returncode,r.stdout,r.stderr)
print(f'packed checking: {len(cases)} checks passed')
