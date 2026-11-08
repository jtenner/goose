from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;q=p/'parent03';q.mkdir(exist_ok=True);r=Path('/home/dev/Projects/goose-wasm-backend');exe='/tmp/goose-wasm-limited-array-conversion-20261108/build02/goose-tested';cases={}
for kind,shape in [('fixed','[2]'),('limited','[..3]')]:
 t='u8'+shape;rt='S&'+shape
 cases[kind+'_inline_opaque']=f'var source:{t}=[7,8];recursive fn read(a:bool&)->bool{{return a;}}inline fn pick(yes:bool)->i64{{var b:u8[]=({{if yes{{return 42 from pick;}}source}});return b[1];}}fn main(){{var yes=true;var no=false;assert(pick(read(yes))==42);print("true");assert(pick(read(no))==8);print("false");print("opaque");}}\n'
 cases[kind+'_defer_refs']=f'struct S{{n:i64}}var first=S{{1}};var second=S{{2}};var source:{rt}=[first,second];fn main(){{var b:S&[]=({{defer source[0] .= second;source}});assert(b.len==2&&b[0] .== &first&&source[0] .== &second&&b[1] .== &second);print("defer_refs");}}\n'
cases['mixed_fixed']='recursive fn probe(yes:bool){var a:u8[2]=[7,8];var c:u8[3]=[9,10,11];var b:u8[]=if yes{a}else{c};assert(b.len==(if yes{2}else{3}));}fn main(){probe(true);probe(false);print("mixed");}\n'
cases['mixed_limited']='recursive fn probe(yes:bool){var a:u8[..3]=[7,8];var c:u8[..4]=[9,10,11,12];var b:u8[]=if yes{a}else{c};assert(b.len==(if yes{2}else{4}));}fn main(){probe(true);probe(false);print("mixed");}\n'
rows=[]
for name,source in cases.items():
 f=q/(name+'.goose');f.write_text(source);row={'case':name,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
 for kind,args in [('emit',[exe,'--standalone','-o',q/(name+'.c'),f]),('cc',['cc',q/(name+'.c'),'-pthread','-lm','-ldl','-o',q/(name+'.native')]),('native',[q/(name+'.native')]),('wasm',[exe,'-O0','--target','wasm','-o',q/(name+'.wasm'),f])]:
  args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120);row[kind+'_exit']=a.returncode
  for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (q/(name+'-'+kind+'.'+k)).write_bytes(v)
  (q/(name+'-'+kind+'.json')).write_text(json.dumps(args)+'\n')
  if a.returncode and kind!='wasm':break
 if row.get('native_exit')==0 and not name.startswith('mixed_'):
  (r/'test/wasm'/('wasm_array_expression_source_'+name+'.goose')).write_bytes(f.read_bytes());(r/'test/expected'/('wasm_array_expression_source_'+name+'.out')).write_bytes((q/(name+'-native.stdout')).read_bytes())
 rows.append(row)
(q/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows)
q=p/'focused02';q.mkdir(exist_ok=True);s=(p/'focused01/checks.py').read_text().replace("glob('wasm_array_expression_source_*.goose')", "glob('wasm_array_expression_source_*_opaque.goose')")
s=s.replace("sources=sorted((r/'test/wasm').glob('wasm_array_expression_source_*_opaque.goose'))", "sources=sorted(list((r/'test/wasm').glob('wasm_array_expression_source_*_opaque.goose'))+list((r/'test/wasm').glob('wasm_array_expression_source_*_defer_refs.goose')))")
(q/'checks.py').write_text(s)
