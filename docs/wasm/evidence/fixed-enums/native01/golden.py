from pathlib import Path
import subprocess,json,hashlib,sys
p=Path(__file__).parent.parent;o=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');exe=Path('/tmp/goose-wasm-fixed-struct-20261107/build04/goose-tested');cases=json.loads((p/'fixture-names.json').read_text());rows=[];failed=[]
assert hashlib.sha256(exe.read_bytes()).hexdigest()=='7fdb4c2236fcfddb599c0426e23ba5547779ec0ef0f27790545a886b4edd1d54'
def run(name,args):
 args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=90)
 for ext,d in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (o/(name+'.'+ext)).write_bytes(d)
 rows.append({'name':name,'command':args,'exit':a.returncode});(o/'results.json').write_text(json.dumps(rows,indent=2)+'\n');return a
for case in cases:
 for opt in [0,2]:
  name=case+'-O'+str(opt);source=p/(case+'.goose');c=o/(name+'.c');native=o/(name+'.native');w=o/(name+'-before.wasm')
  a=run(name+'-native-emit',[exe,'-O'+str(opt),'--standalone','-o',c,source])
  if a.returncode:failed.append(name+' native emit');continue
  a=run(name+'-native-build',['cc','-O0',c,'-pthread','-lm','-ldl','-o',native])
  if a.returncode:failed.append(name+' native build');continue
  a=run(name+'-native-run',[native])
  if a.returncode:failed.append(name+' native run');continue
  a=run(name+'-prior-wasm',[exe,'-O'+str(opt),'--target','wasm','-o',w,source])
  if not a.returncode or w.exists() or not any(reason in a.stderr for reason in [b'this value layout is not implemented (scalar backend)',b'this fixed field layout needs the pending layout lowering']):failed.append(name+' prior target reason')
 a=o/(case+'-O0-native-run.stdout');b=o/(case+'-O2-native-run.stdout')
 if a.exists() and b.exists() and a.read_bytes()!=b.read_bytes():failed.append(case+' optimization outputs differ')
(o/'summary.json').write_text(json.dumps({'compiler_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'sources':{n:hashlib.sha256((p/(n+'.goose')).read_bytes()).hexdigest() for n in cases},'failed':failed},indent=2)+'\n');print(json.dumps({'failed':failed},indent=2));sys.exit(bool(failed))
