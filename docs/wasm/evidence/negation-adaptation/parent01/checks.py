from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');exe=Path('/tmp/goose-native-math-adaptation-20261108/build01/goose-tested');rows=[]
def run(stem,args):
 a=subprocess.run(list(map(str,args)),cwd=r,capture_output=True,timeout=120)
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(stem+'.'+k)).write_bytes(v)
 return a
for name in json.loads((p.parent/'cases.json').read_text()):
 f=p/(name+'.goose');c=p/(name+'.c');native=p/(name+'.native');wasm=p/(name+'.wasm')
 a=run(name+'-emit',[exe,'-O0','--standalone','-o',c,f]);assert not a.returncode,(name,a.stderr)
 a=run(name+'-cc',['cc',c,'-pthread','-lm','-ldl','-o',native]);assert not a.returncode,a.stderr
 a=run(name+'-native',[native]);assert not a.returncode and a.stdout==name.encode()+b'\n',(name,a)
 a=run(name+'-wasm',[exe,'-O0','--target','wasm','-o',wasm,f]);assert a.returncode!=0 and not wasm.exists(),(name,a)
 rows.append({'case':name,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'native':'PASS','wasm_exit':a.returncode,'wasm_reason':a.stderr.decode()})
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS',len(rows),'native-valid Wasm failures recorded')
