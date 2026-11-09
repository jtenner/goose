from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');out=p/'assert-limits01';out.mkdir(exist_ok=True);before=p/'limits01/artifacts';exe=p/'assert-build01/goose-tested';identity=json.loads((p/'assert-build01/compiler-identity.json').read_text());assert hashlib.sha256(exe.read_bytes()).hexdigest()==identity['sha256'];assert (p/'limits01/check.exit').read_text().strip()=='0';rows=[];commands=[]
def run(args):
 args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120);commands.append({'command':args,'exit':a.returncode,'stdout':a.stdout.decode(errors='replace'),'stderr':a.stderr.decode(errors='replace')});(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');return a
for x in json.loads((p/'limit-families.json').read_text()):
 name=x['case'].replace('_','-');source=before/('data-fill-limit-'+name+'.goose');assert hashlib.sha256(source.read_bytes()).hexdigest()==x['source_sha256']
 for opt in (0,2):
  module=out/f'data-fill-limit-{name}-O{opt}.wasm';a=run([exe,f'-O{opt}','--target','wasm','-o',module,source])
  if x['expected_candidate_rejection']:assert a.returncode==1 and x['expected_candidate_rejection'].encode() in a.stderr and not module.exists()
  else:
   assert not a.returncode and not a.stderr
   release=before/module.name;assert module.read_bytes()==release.read_bytes();b=run(['node',r/'test/wasm_reference_abi.mjs',module,out/f'{name}-O{opt}-instance']);assert not b.returncode and b.stdout==b'guard\n' and not b.stderr
  rows.append({'case':name,'opt':opt,'status':'PASS','kind':'matching exact rejection' if x['expected_candidate_rejection'] else 'Release byte-identical and Node PASS'})
(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n');assert len(rows)==8;print('PASS8 assertion-enabled count-boundary compiler checks')
