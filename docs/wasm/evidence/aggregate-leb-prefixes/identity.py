from pathlib import Path
import json,hashlib,subprocess
raw=Path(__file__).parent;p=raw/'identity01';p.mkdir(exist_ok=True);r=Path('/home/dev/Projects/goose-wasm-backend');old=Path('/tmp/goose-wasm-aggregate-data-fill-20261109');identity=json.loads((raw/'compiler-identity.json').read_text());exe=identity['compiler']
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
proof=json.loads((old/'full-correctness01/fixture-reuse.json').read_text());assert proof['status']=='PASS verified fixture reuse; fresh core and all suffix checks passed';assert (old/'full-correctness01/check.exit').read_text().strip()=='0';oldinputs=json.loads((old/'validation-inputs.json').read_text());rows=[];commands=[]
assert sha(exe)==identity['sha256']
for rec in proof['fixtures']:
 source=r/rec['source'];assert sha(source)==oldinputs[rec['source']];name=source.stem+f"-O{rec['opt']}.wasm";before=old/'full-correctness01/artifacts'/name;after=p/name;assert sha(before)==rec['sha256']
 args=list(map(str,[exe,f"-O{rec['opt']}",'--target','wasm','-o',after,source]));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120);commands.append({'command':args,'exit':a.returncode,'stdout':a.stdout.decode(errors='replace'),'stderr':a.stderr.decode(errors='replace')});assert not a.returncode,(args,a.stderr)
 h=sha(after);rows.append({'source':rec['source'],'opt':rec['opt'],'parent':str(before),'parent_sha256':rec['sha256'],'sha256':h,'status':'identical' if h==rec['sha256'] else 'changed'})
 if len(rows)%100==0 or h!=rec['sha256']:
  (p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');(p/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 assert h==rec['sha256'],rows[-1]
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');(p/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');assert len(rows)==1978;print('PASS',len(rows),'old modules byte-identical to executed parent fixtures')
