from pathlib import Path
import hashlib,json,subprocess,sys
p=Path(__file__).parent;root=p.parent;repo=Path('/home/dev/Projects/goose-wasm-backend')
exe=Path('/tmp/goose-wasm-fixed-aggregate-arrays-20261107/build02/goose-tested')
assert hashlib.sha256(exe.read_bytes()).hexdigest()=='bd3856b6c2eedd69bd4eaf343aa9f505794f1a17ab3383194b218fbe33fa368d'
rows=[];failures=[]
def run(name,cmd):
 a=subprocess.run(list(map(str,cmd)),cwd=repo,capture_output=True,timeout=120)
 for ext,value in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]:
  with (p/(name+'.'+ext)).open('xb') as f:f.write(value)
 rows.append({'name':name,'command':list(map(str,cmd)),'exit':a.returncode});(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');return a
for name in ['enums']:
 source=p/(name+'.goose');source.write_bytes((root/(name+'.goose')).read_bytes())
 for opt in [0,2]:
  stem=name+'-O'+str(opt);c=p/(stem+'.c');native=p/(stem+'.native');wasm=p/(stem+'.wasm')
  a=run(stem+'-native-emit',[exe,'-O'+str(opt),'--standalone','-o',c,source])
  if a.returncode:failures.append(stem+' native source');continue
  a=run(stem+'-native-build',['cc','-O0',c,'-pthread','-lm','-ldl','-o',native])
  if a.returncode:failures.append(stem+' native build');continue
  a=run(stem+'-native-run',[native])
  if a.returncode or a.stderr:failures.append(stem+' native run');continue
  if opt==0:(p/(name+'.expected')).write_bytes(a.stdout)
  elif a.stdout!=(p/(name+'.expected')).read_bytes():failures.append(stem+' native mismatch')
  prior=run(stem+'-prior-wasm',[exe,'-O'+str(opt),'--target','wasm','-o',wasm,source])
  if not prior.returncode or b'by-value aggregate iteration needs the pending destination lowering' not in prior.stderr or wasm.exists():failures.append(stem+' exact parent gate')
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');(p/'summary.json').write_text(json.dumps({'commands':len(rows),'failed':failures},indent=2)+'\n')
print(json.dumps({'commands':len(rows),'failed':failures}),flush=True);sys.exit(bool(failures))
