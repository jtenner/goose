from pathlib import Path
import subprocess,hashlib,json
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');out=p/'parent02';out.mkdir(exist_ok=True);identity=json.loads((p/'parent-compiler-identity.json').read_text());exe=identity['compiler'];assert hashlib.sha256(Path(exe).read_bytes()).hexdigest()==identity['sha256'];rows=[];i=0
def run(args):
 global i
 i+=1;args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120);prefix=out/f'command-{i:04}';prefix.with_suffix('.json').write_text(json.dumps(args)+'\n');prefix.with_suffix('.stdout').write_bytes(a.stdout);prefix.with_suffix('.stderr').write_bytes(a.stderr);prefix.with_suffix('.exit').write_text(str(a.returncode)+'\n');return a,i
for x in json.loads((p/'parent01/results.json').read_text()):
 f=p/'prepared'/(x['case']+'.goose');assert hashlib.sha256(f.read_bytes()).hexdigest()==x['source_sha256']
 for label,index in x['commands'].items():
  prefix=p/'parent01'/f'command-{index:04}';assert int(prefix.with_suffix('.exit').read_text())==(1 if label=='wasm' else 0)
  if label=='native':assert prefix.with_suffix('.stdout').read_bytes()==x['expected'].encode() and not prefix.with_suffix('.stderr').read_bytes()
 rows.append(x)
for record in json.loads((p/'prepared-families.json').read_text()):
 if record['case'] in {x['case'] for x in rows}:continue
 f=p/'prepared'/(record['case']+'.goose')
 expected=record['expected'].encode();c=out/(f.stem+'.c');native=out/(f.stem+'.native');wasm=out/(f.stem+'.wasm');commands={}
 for label,args in [('emit',[exe,'-O0','--standalone','-o',c,f]),('cc',['cc','-O0',c,'-pthread','-lm','-ldl','-o',native]),('native',[native]),('wasm',[exe,'-O0','--target','wasm','-o',wasm,f])]:
  a,index=run(args);commands[label]=index
  if label=='wasm':assert a.returncode==1 and b'compound array elements need the pending layout lowering' in a.stderr and not wasm.exists(),(f.name,a.returncode,a.stderr)
  else:
   assert a.returncode==0,(f.name,label,a.returncode,a.stderr)
   if label=='native':assert a.stdout==expected and not a.stderr,(f.name,a.stdout,a.stderr)
 rows.append({'case':f.stem,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'expected':expected.decode(),'commands':commands,'producer_phase':'parent02','status':'PASS native; parent Wasm LEB compound rejection'});(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print('PASS',len(rows),'native-valid aggregate LEB failures')
