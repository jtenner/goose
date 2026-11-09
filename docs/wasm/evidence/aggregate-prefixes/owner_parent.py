from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;q=p/'parent04';q.mkdir(exist_ok=True);r=Path('/home/dev/Projects/goose-wasm-backend');exe=Path('/tmp/goose-wasm-array-prefix-conversion-20261108/build01/goose-tested');cases={}
for prefix in ['u8','u16','u64']:
 cases['owner_'+prefix]='struct S{mark:u8,cells:u16[2],limited:u16[..3],tail:u8}'+f'recursive fn check(rows:S[{prefix}]&)->bool{{return rows.len==2&&rows[0].mark==1&&rows[0].cells[1]==22&&rows[0].limited.len==2&&rows[0].limited[1]==44&&rows[1].limited.len==0&&rows[1].tail==4;}}fn main(){{print("before");var rows:S[{prefix}]=[S{{1,[11,22],[33,44],2}},S{{3,[55,66],[],4}}];print("after");assert(check(rows));}}\n'

rows=[]
for name,source in cases.items():
 f=q/(name+'.goose');f.write_text(source);row={'case':name,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
 for kind,args in [('emit',[exe,'--standalone','-o',q/(name+'.c'),f]),('cc',['cc',q/(name+'.c'),'-pthread','-lm','-ldl','-o',q/(name+'.native')]),('native',[q/(name+'.native')]),('wasm',[exe,'-O0','--target','wasm','-o',q/(name+'.wasm'),f])]:
  args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120);row[kind+'_exit']=a.returncode
  (q/(name+'-'+kind+'.json')).write_text(json.dumps(args)+'\n')
  for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (q/(name+'-'+kind+'.'+k)).write_bytes(v)
  if a.returncode and kind!='wasm':break
 rows.append(row)
(q/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
