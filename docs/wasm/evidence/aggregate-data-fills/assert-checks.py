from pathlib import Path
import subprocess,json,hashlib
raw=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');p=raw/'assert-check01';p.mkdir(exist_ok=True);exe=raw/'assert-build01/goose-tested';rows=[];commands=[]
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def run(args):
 args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120);commands.append({'command':args,'exit':a.returncode,'stdout':a.stdout.decode(errors='replace'),'stderr':a.stderr.decode(errors='replace')});(p/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');assert a.returncode==0,(args,a.stderr);return a
for phase in ['focused01','focused02']:
 assert (raw/phase/'check.exit').read_text().strip()=='0'
 for rec in json.loads((raw/phase/'results.json').read_text()):
  name=rec['case'];opt=rec['opt'];src=r/'test/wasm'/(name+'.goose');assert sha(src)==rec['source_sha256'];before=raw/phase/(name+f'-O{opt}.wasm');assert sha(before)==rec['wasm_sha256'];out=p/before.name
  run([exe,f'-O{opt}','--target','wasm','-o',out,src]);assert sha(out)==rec['wasm_sha256'];a=run(['node',r/'test/wasm_reference_abi.mjs',out,p/(name+f'-O{opt}-instance')]);expected=r/'test/expected'/(name+'.out');assert a.stdout==expected.read_bytes() and not a.stderr
  rows.append({'source':str(src.relative_to(r)),'opt':opt,'sha256':sha(out),'status':'PASS assertions enabled and Release byte identity'})
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');assert len(rows)==86;print('PASS',len(rows),'assertion compiler/Node pairs, all Release byte-identical')
