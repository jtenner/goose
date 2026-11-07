from pathlib import Path
import subprocess,json,sys
p=Path(__file__).parent;root=p.parent;r=Path('/home/dev/Projects/goose-wasm-backend');exe=Path('/tmp/goose-wasm-fixed-enum-20261107/build02/goose-tested');rows=[];failed=[]
def run(name,args):
 args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=180)
 for ext,d in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]:
  with (p/(name+'.'+ext)).open('xb') as f:f.write(d)
 rows.append({'name':name,'command':args,'exit':a.returncode});(p/'native-results.json').write_text(json.dumps(rows,indent=2)+'\n');return a
cases={name:source for name,(source,_) in json.loads((root/'gate-cases.json').read_text()).items()};cases['global-effects']=(root/'global-effects.goose').read_text()
for name,text in cases.items():
 source=p/(name+'.goose');source.write_text(text)
 for opt in [0,2]:
  stem='native-'+name+'-O'+str(opt);c=p/(stem+'.c');binary=p/(stem+'.native')
  a=run(stem+'-emit',[exe,'-O'+str(opt),'--standalone','-o',c,source])
  if a.returncode:failed.append(stem+' emit');continue
  a=run(stem+'-build',['cc','-O0',c,'-pthread','-lm','-ldl','-o',binary])
  if a.returncode:failed.append(stem+' build');continue
  a=run(stem+'-run',[binary])
  if a.returncode:failed.append(stem+' run')
(p/'native-summary.json').write_text(json.dumps({'failed':failed},indent=2)+'\n');print(json.dumps({'failed':failed}));sys.exit(bool(failed))
