from pathlib import Path
import json,hashlib,subprocess,shutil
p=Path(__file__).parent;raw=p.parent;old=raw/'parent01';r=Path('/home/dev/Projects/goose-wasm-backend');exe=Path('/tmp/goose-native-math-adaptation-20261108/build01/goose-tested');rows=[]
original=json.loads((raw/'cases.json').read_text());shutil.copy2(raw/'cases.json',raw/'cases-original01.json')
cases=dict(original);cases['nested']=cases['nested'].replace('x:i64,y:f32','x:f32,y:f32')
(raw/'cases02.json').write_text(json.dumps(cases,indent=2)+'\n')
def run(stem,args):
 a=subprocess.run(list(map(str,args)),cwd=r,capture_output=True,timeout=120)
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(stem+'.'+k)).write_bytes(v)
 return a
for name,source in cases.items():
 if name not in ['nested','array']:
  f=old/(name+'.goose');assert f.read_text()==source+'\n'
  for phase in ['emit','cc','native']:assert (old/(name+'-'+phase+'.exit')).read_text().strip()=='0'
  assert (old/(name+'-native.stdout')).read_bytes()==name.encode()+b'\n'
  assert (old/(name+'-wasm.exit')).read_text().strip()!='0' and not (old/(name+'.wasm')).exists()
  reason=(old/(name+'-wasm.stderr')).read_text()
  assert 'fixed negation' in reason,reason
  rows.append({'case':name,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'reused':str(old),'reason':reason});continue
 f=p/(name+'.goose');f.write_text(source+'\n');c=p/(name+'.c');native=p/(name+'.native');wasm=p/(name+'.wasm')
 a=run(name+'-emit',[exe,'-O0','--standalone','-o',c,f]);assert not a.returncode,(name,a.stderr)
 a=run(name+'-cc',['cc',c,'-pthread','-lm','-ldl','-o',native]);assert not a.returncode,a.stderr
 a=run(name+'-native',[native]);assert not a.returncode and a.stdout==name.encode()+b'\n',(name,a)
 a=run(name+'-wasm',[exe,'-O0','--target','wasm','-o',wasm,f]);assert a.returncode!=0 and b'fixed negation' in a.stderr and not wasm.exists(),(name,a)
 rows.append({'case':name,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'reason':a.stderr.decode()})
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS',len(rows),'native-valid Wasm exact-layout failures;8 reused/no rerun')
