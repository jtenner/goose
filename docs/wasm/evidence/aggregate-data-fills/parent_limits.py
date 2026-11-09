from pathlib import Path
import json,hashlib,subprocess
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');out=p/'parent-limits01';out.mkdir(exist_ok=True);identity=json.loads((p/'parent-compiler-identity.json').read_text());exe=identity['compiler'];assert hashlib.sha256(Path(exe).read_bytes()).hexdigest()==identity['sha256'];rows=[];i=0
def run(args):
 global i
 i+=1;args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120);f=out/f'command-{i:04}';f.with_suffix('.json').write_text(json.dumps(args)+'\n');f.with_suffix('.stdout').write_bytes(a.stdout);f.with_suffix('.stderr').write_bytes(a.stderr);f.with_suffix('.exit').write_text(str(a.returncode)+'\n');return a,i
for x in json.loads((p/'limit-families.json').read_text()):
 f=p/'limit-sources'/(x['case']+'.goose');assert hashlib.sha256(f.read_bytes()).hexdigest()==x['source_sha256'];c=out/(f.stem+'.c');native=out/(f.stem+'.native');module=out/(f.stem+'.wasm');commands={}
 for label,args in [('emit',[exe,'-O0','--standalone','-o',c,f]),('cc',['cc','-O0',c,'-pthread','-lm','-ldl','-o',native]),('native',[native]),('wasm',[exe,'-O0','--target','wasm','-o',module,f])]:
  a,index=run(args);commands[label]=index
  if label=='wasm':assert a.returncode==1 and b'aggregate data fills need the pending snapshot lowering' in a.stderr and not module.exists(),a.stderr
  else:
   assert not a.returncode,(f.name,label,a.stderr)
   if label=='native':assert a.stdout==b'guard\n' and not a.stderr,(f.name,a.stdout,a.stderr)
 rows.append({**x,'commands':commands,'status':'PASS native runtime-false path; parent Wasm fill guard'});(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print('PASS4 native-valid count-boundary programs; false branch avoids all large allocations')
