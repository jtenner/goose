from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');exe=p.parent/'assert-build02/goose-tested';i=0;rows=[]
def run(args):
 global i
 i+=1;args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120)
 (p/f'command-{i:04}.json').write_text(json.dumps(args)+'\n')
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(f'command-{i:04}.'+k)).write_bytes(v)
 assert a.returncode==0,(args,a.returncode,a.stderr)
 return a
for source in sorted((r/'test/wasm').glob('wasm_aggregate_prefix_*.goose')):
 for opt in [0,2]:
  module=p/(source.stem+f'-O{opt}.wasm');run([exe,f'-O{opt}','--target','wasm','-o',module,source]);run(['wasm-tools','validate',module]);a=run(['node',r/'scripts/run_wasm.mjs',module]);assert a.stdout==(r/'test/expected'/(source.stem+'.out')).read_bytes() and not a.stderr
  reference=p.parent/('focused04' if source.stem.endswith('_owner_dynamic') else 'focused05' if source.stem.endswith(('_u8_255','_u16_256')) else 'focused03')/module.name;assert module.read_bytes()==reference.read_bytes(),source
  rows.append({'case':source.stem,'opt':opt,'sha256':hashlib.sha256(module.read_bytes()).hexdigest(),'status':'PASS byte-identical with assertions enabled'})
assert len(rows)==154,len(rows)
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS',len(rows),'assert-enabled compiler/Node pairs and Release byte identities')
