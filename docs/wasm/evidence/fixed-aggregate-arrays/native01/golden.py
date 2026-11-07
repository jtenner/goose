from pathlib import Path
import subprocess,json,hashlib,sys
p=Path(__file__).parent;root=p.parent;r=Path('/home/dev/Projects/goose-wasm-backend');exe=Path('/tmp/goose-wasm-fixed-enum-20261107/build02/goose-tested');rows=[];failed=[]
assert hashlib.sha256(exe.read_bytes()).hexdigest()=='250902481fe28fadfd7102f7ac64475814c864dbc91ff2060ce5b9ed360eb73c'
def run(name,args):
 args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=180)
 for ext,d in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]:
  with (p/(name+'.'+ext)).open('xb') as f:f.write(d)
 rows.append({'name':name,'command':args,'exit':a.returncode});(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');return a
for case in json.loads((root/'fixture-names.json').read_text()):
 for opt in [0,2]:
  name=case+'-O'+str(opt);source=root/(case+'.goose');c=p/(name+'.c');binary=p/(name+'.native');w=p/(name+'.wasm')
  a=run(name+'-native-emit',[exe,'-O'+str(opt),'--standalone','-o',c,source])
  if a.returncode:failed.append(name+' native emit');continue
  a=run(name+'-native-build',['cc','-O0',c,'-pthread','-lm','-ldl','-o',binary])
  if a.returncode:failed.append(name+' native build');continue
  a=run(name+'-native-run',[binary])
  if a.returncode:failed.append(name+' native run');continue
  a=run(name+'-before',[exe,'-O'+str(opt),'--target','wasm','-o',w,source])
  if not a.returncode or w.exists() or not any(x in a.stderr for x in [b'compound array elements',b'this fixed field layout needs']):failed.append(name+' prior target reason')
 a=p/(case+'-O0-native-run.stdout');b=p/(case+'-O2-native-run.stdout')
 if a.exists() and b.exists() and a.read_bytes()!=b.read_bytes():failed.append(case+' optimization output mismatch')
(p/'summary.json').write_text(json.dumps({'failed':failed,'compiler_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'sources':{name:hashlib.sha256((root/(name+'.goose')).read_bytes()).hexdigest() for name in json.loads((root/'fixture-names.json').read_text())}},indent=2)+'\n');print(json.dumps({'failed':failed}));sys.exit(bool(failed))
