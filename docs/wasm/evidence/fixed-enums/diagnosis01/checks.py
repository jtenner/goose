from pathlib import Path
import subprocess,json,hashlib,sys
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');old=Path('/tmp/goose-wasm-fixed-struct-20261107/build04/goose-tested');candidate=p.parent/'build01/goose-tested';rows=[];failed=[]
def run(name,args):
 args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120)
 for ext,d in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]:
  with (p/(name+'.'+ext)).open('xb') as f:f.write(d)
 rows.append({'name':name,'command':args,'exit':a.returncode});(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');return a
for case in json.loads((p/'names.json').read_text()):
 for opt in [0,2]:
  name=case+'-O'+str(opt);source=p/(case+'.goose');c=p/(name+'.c');native=p/(name+'.native')
  a=run(name+'-native-emit',[old,'-O'+str(opt),'--standalone','-o',c,source])
  if a.returncode:failed.append(name+' invalid source');continue
  a=run(name+'-native-build',['cc','-O0',c,'-pthread','-lm','-ldl','-o',native])
  if a.returncode:failed.append(name+' native setup');continue
  a=run(name+'-native-run',[native])
  if a.returncode:failed.append(name+' native failed');continue
  for which,exe in [('prior',old),('before',candidate)]:
   w=p/(name+'-'+which+'.wasm');a=run(name+'-'+which,[exe,'-O'+str(opt),'--target','wasm','-o',w,source])
   if case=='enum-callback-match' and which=='prior':continue
   if not a.returncode or b'out-of-line captured locals are not implemented' not in a.stderr:failed.append(name+' '+which+' missing expected failure')
(p/'summary.json').write_text(json.dumps({'failed':failed,'rows':len(rows)},indent=2)+'\n');print(json.dumps({'failed':failed,'rows':len(rows)}));sys.exit(bool(failed))
