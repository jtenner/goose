from pathlib import Path
import subprocess,json,hashlib,shutil
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path('/tmp/goose-wasm-byte-strings-20261107');compiler=Path('/tmp/goose-wasm-array-fills-20261107/goose-tested');rows=[]
def run(name,args,ok=True):
 args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=90)
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(name+'.'+ext)).write_bytes(data)
 rows.append({'name':name,'command':args,'exit':a.returncode});(p/'golden-results.json').write_text(json.dumps(rows,indent=2)+'\n')
 assert not ok or a.returncode==0,(name,a.stderr)
 return a
for case in ['construct','printing']:
 for opt in [0,2]:
  n=case+'-O'+str(opt);source=p/(case+'.goose');c=p/(n+'.c');exe=p/(n+'.native');w=p/(n+'-before.wasm')
  run(n+'-native-emit',[compiler,'-O'+str(opt),'--standalone','-o',c,source]);run(n+'-native-build',['cc','-O0',c,'-pthread','-lm','-ldl','-o',exe]);run(n+'-native-run',[exe])
  a=run(n+'-prior-wasm',[compiler,'-O'+str(opt),'--target','wasm','-o',w,source],ok=False)
  reason=b'this array constructor needs the pending destination lowering' if case=='construct' else b'printing this value layout is not implemented'
  assert a.returncode and reason in a.stderr,(n,a.stderr)
  assert not w.exists()
 assert (p/(case+'-O0-native-run.stdout')).read_bytes()==(p/(case+'-O2-native-run.stdout')).read_bytes()
(p/'golden-identities.json').write_text(json.dumps({'compiler_sha256':hashlib.sha256(compiler.read_bytes()).hexdigest(),'sources':{case:hashlib.sha256((p/(case+'.goose')).read_bytes()).hexdigest() for case in ['construct','printing']}},indent=2)+'\n')
print('Native-valid inputs and prior target behavior recorded')
assert b'capture=abc|0|Xbc\n' in (p/'printing-O0-native-run.stdout').read_bytes()
