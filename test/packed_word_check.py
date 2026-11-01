#!/usr/bin/env python3
"""Packed-word diagnostics and selected-branch semantic checks."""
import subprocess,tempfile,pathlib,os
cases=[
('packed word W:u8 {a:u2,_:u6} fn main(){var w=W{a:1}; w.a=2;}',None),
('packed word W:u8 {a:u6,b:u3} fn main(){}','uses 9 bits'),
('packed word W:u8 {a:u2,a:bool} fn main(){}','duplicate field'),
('packed word W:u8 {a:u0} fn main(){}','between 1 and 64'),
('packed word W:u8 {a:u129} fn main(){}','between 1 and 64'),
('packed word W:u8 {a:i3} fn main(){}','signed packed'),
('packed word W:u8 {a:u2} fn main(){var w=W{a:4};}','does not fit packed word'),
('packed word W:u8 {a:u2} fn main(){let w=W{a:1}; w.a=2;}','let'),
('packed word W:u8 {a:u2} fn main(){var w=W{a:1}; let r=&w.a;}','not addressable'),
('packed word W:u8 {a:u2} fn f(x:u8&){} fn main(){var w=W{a:1}; f(w.a);}','not addressable'),
('packed word W:u8 {const if false {a:u129} else {a:u2},_:u6} fn main(){var w=W{a:1};}',None),
('packed word W:u64 {a:u64} fn main(){var w=W{a:18446744073709551615};}',None),
('enum E{A,B,C} packed word W:u8 {e:E,_:u6} fn main(){var w=W{e:E.B};}',None),
('enum E{A{x:u8}} packed word W:u8 {e:E} fn main(){}','payload-free'),
('packed word W:u8 {a:u2} fn main(){var w=W{a:1}; let r=w as u8; let v=r as W;}',None),
('packed word W:u8 {a:u2} fn main(){var w=W{a:1}; let r=w as u64;}','exact backing'),
]
for field in ('x:i8', 'x:u8[2]', 'x:u8&', 'x:f64', 'x:W'):
 cases.append((f'packed word W:u64 {{{field}}} fn main(){{}}', 'packed word'))
for backing in ('i64','u7','u256','bool'):
 cases.append((f'packed word W:{backing} {{x:u1}} fn main(){{}}','backing'))
cases += [
 ('packed word W:u8 {a:u2} fn main(){var w=W{1}; print(w._);}', 'reserved'),
 ('packed word W:u8 {a:u2} fn main(){var w=W{_:1};}', 'reserved'),
 ('packed word W:u8 {a:u2} fn main(){var w=W{};}', 'missing'),
 ('packed word W:u8 {a:u2} fn main(){var w=W{a:1,a:2};}', 'duplicate'),
 ('packed word W:u8 {a:u2} fn main(){var w=W{1}; var x:i64=1; w.a=x;}', 'unsigned'),
 ('packed word W:u8 {b:bool} fn main(){var w=W{true}; w.b+=true;}', 'plain assignment'),
 ('packed word W:u8 {b:bool} fn main(){var w=W{1};}', 'bool'),
 ('packed word W:u8 {a:u2} packed word V:u8 {a:u2} fn main(){var w=W{1}; var v:V=w;}', 'V'),
 ('packed word W:u8 {a:u2} fn main(){var w:W; w.a=1;}', 'before it is assigned'),
 ('packed word W:u8 {a:u2, const if true {a:u2}} fn main(){}', 'duplicate'),
 ('packed word W:u8 {a:u2, const if false {a:u129}} fn main(){}', None),
 ('packed word W:u8 {const if false {a: }} fn main(){}', 'type'),
 ('packed word W:u8 {a:u2} fn take<T>(x:T&){} fn main(){var w=W{1}; take(w.a);}', 'not addressable'),
]
with tempfile.TemporaryDirectory(prefix='packed-check-') as td:
 for i,(source,expected) in enumerate(cases):
  p=pathlib.Path(td)/f'{i}.goose';p.write_text(source)
  r=subprocess.run([os.environ.get('GOOSE_TEST_EXE','goose++'),'--check',str(p)],capture_output=True,text=True)
  assert (r.returncode==0)==(expected is None) and (expected is None or expected in r.stderr+r.stdout),(i,r.returncode,r.stdout,r.stderr)
print(f'packed checking: {len(cases)} checks passed')
