from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');out=p/'focused01';out.mkdir(exist_ok=True);identity=json.loads((p/'compiler-identity.json').read_text());exe=identity['compiler'];assert hashlib.sha256(Path(exe).read_bytes()).hexdigest()==identity['sha256'];i=0;rows=[]
def run(args):
 global i
 i+=1;args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120);prefix=out/f'command-{i:04}';prefix.with_suffix('.json').write_text(json.dumps(args)+'\n');prefix.with_suffix('.stdout').write_bytes(a.stdout);prefix.with_suffix('.stderr').write_bytes(a.stderr);prefix.with_suffix('.exit').write_text(str(a.returncode)+'\n');assert not a.returncode,(args,a.returncode,a.stderr);return a
for x in json.loads((p/'positive-families.json').read_text()):
 f=r/'test/wasm'/(x['fixture']+'.goose');expected=x['expected'].encode();assert hashlib.sha256(f.read_bytes()).hexdigest()==x['source_sha256']
 for opt in (0,2):
  prefix=out/(f.stem+f'-O{opt}');c,native,wasm=[prefix.with_suffix(e) for e in ['.c','.native','.wasm']]
  run([exe,f'-O{opt}','--standalone','-o',c,f]);run(['cc',f'-O{opt}',c,'-pthread','-lm','-ldl','-o',native]);a=run([native]);assert a.stdout==expected and not a.stderr
  run([exe,f'-O{opt}','--target','wasm','-o',wasm,f]);run(['wasm-tools','validate',wasm])
  for host,args in [('node',['node',r/'test/wasm_reference_abi.mjs',wasm,out/(f.stem+f'-O{opt}-instance')]),('wasmtime',['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',wasm]),('owner',['node',r/'test/wasm_multimemory.mjs',wasm,str(x['persistent'])])]:
   a=run(args);assert a.stdout==expected and not a.stderr,(f.name,opt,host,a.stdout,a.stderr)
  rows.append({'case':f.stem,'opt':opt,'source_sha256':x['source_sha256'],'wasm_sha256':hashlib.sha256(wasm.read_bytes()).hexdigest(),'status':'PASS'});(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print('PASS',len(rows),'native/Node/Wasmtime and completed-owner pairs')
