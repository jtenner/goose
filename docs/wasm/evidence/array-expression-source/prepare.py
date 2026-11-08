from pathlib import Path
import subprocess,json,hashlib,shutil
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path('/tmp/goose-wasm-array-expression-source-20261108');p.mkdir(exist_ok=True);q=p/'parent01';q.mkdir(exist_ok=True)
shutil.copy2('/tmp/goose-wasm-limited-array-conversion-20261108/run_suite.py',p/'run_suite.py');shutil.copy2(__file__,p/'prepare.py');exe=Path('/tmp/goose-wasm-limited-array-conversion-20261108/build02/goose-tested');cases={}
for kind,shape in [('fixed','[2]'),('limited','[..3]')]:
 t='u8'+shape;other='[9,10]' if kind=='fixed' else '[9]';third='[11,12]' if kind=='fixed' else '[]'
 cases[kind+'_block']=f'fn main(){{var b:u8[]=({{var a:{t}=[7,8];a}});assert(b.len==2&&b[1]==8);'
 cases[kind+'_nested']=f'fn main(){{var b:u8[]=({{var a:{t}=[7,8];({{a}})}});assert(b.len==2&&b[1]==8);'
 cases[kind+'_conditional']=f'recursive fn probe(yes:bool){{var a:{t}=[7,8];var c:{t}={other};var b:u8[]=if yes{{a}}else{{c}};if yes{{assert(b.len==2&&b[1]==8);}}else{{assert(b.len=={2 if kind=="fixed" else 1}&&b[0]==9);}}}}fn main(){{probe(true);probe(false);'
 cases[kind+'_elseif']=f'recursive fn probe(which:i64){{var a:{t}=[7,8];var c:{t}={other};var d:{t}={third};var b:u8[]=if which==0{{a}}else if which==1{{c}}else{{d}};if which==0{{assert(b.len==2&&b[1]==8);}}else if which==1{{assert(b.len=={2 if kind=="fixed" else 1}&&b[0]==9);}}else{{assert(b.len=={2 if kind=="fixed" else 0});}}}}fn main(){{probe(0);probe(1);probe(2);'
 cases[kind+'_call_leaf']=f'recursive fn make()->{t}{{return[7,8];}}fn main(){{var b:u8[]=({{make()}});assert(b.len==2&&b[1]==8);'
 cases[kind+'_defer']=f'var source:{t}=[209,226];fn main(){{var b:u8[]=({{defer source[0]=99;print("inside");source}});print("after");assert(b.len==2&&b[0]==209&&b[1]==226&&source[0]==99);'
 cases[kind+'_early_return']=f'recursive fn probe(yes:bool)->i64{{var b:u8[]=({{if yes{{return 42;}}var a:{t}=[7,8];a}});return b[1];}}fn main(){{assert(probe(true)==42&&probe(false)==8);'
 cases[kind+'_void_branch']=f'recursive fn probe(yes:bool)->i64{{var a:{t}=[7,8];var b:u8[]=if yes{{return 42;}}else{{a}};return b[1];}}fn main(){{assert(probe(true)==42&&probe(false)==8);'
 cases[kind+'_inline_return']=f'var source:{t}=[7,8];inline fn pick(yes:bool)->i64{{var b:u8[]=({{if yes{{return 42 from pick;}}source}});return b[1];}}fn main(){{assert(pick(true)==42);print("true");assert(pick(false)==8);print("false");'
 cases[kind+'_reference_block']=f'var source:{t}=[7,8];fn main(){{var b:u8[]=copy(({{defer source[0]=99;&source}}));assert(b.len==2&&b[0]==99&&source[0]==99);'
rows=[]
for name,body in cases.items():
 text=body+'}\n' if name.endswith('_defer') else body+f'print("{name}");}}\n'
 f=q/(name+'.goose');f.write_text(text);row={'case':name,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
 for kind,args in [('emit',[exe,'--standalone','-o',q/(name+'.c'),f]),('cc',['cc',q/(name+'.c'),'-pthread','-lm','-ldl','-o',q/(name+'.native')]),('native',[q/(name+'.native')]),('wasm',[exe,'-O0','--target','wasm','-o',q/(name+'.wasm'),f])]:
  args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120);row[kind+'_exit']=a.returncode
  for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (q/(name+'-'+kind+'.'+k)).write_bytes(v)
  (q/(name+'-'+kind+'.json')).write_text(json.dumps(args)+'\n')
  if a.returncode and kind!='wasm':break
 rows.append(row)
(q/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
(p/'parent-compiler-identity.json').write_text(json.dumps({'parent':'c423808c123e8b4b89d82f2640838ac86fe2f21c','compiler':str(exe),'sha256':hashlib.sha256(exe.read_bytes()).hexdigest()},indent=2)+'\n')
