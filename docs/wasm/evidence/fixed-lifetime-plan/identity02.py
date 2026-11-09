from pathlib import Path
import hashlib,json,subprocess
raw=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');out=raw/'identity02';out.mkdir(exist_ok=True)
identity=json.loads((raw/'compiler-identity.json').read_text());exe=Path(identity['compiler'])
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(exe)==identity['sha256']
parent=Path('/tmp/goose-wasm-aggregate-leb-20261109');proof=json.loads((parent/'full-correctness01/fixture-reuse.json').read_text());assert len(proof['fixtures'])==2044
rows=[]
for x in proof['fixtures']:
 f=r/x['source'];before=parent/'full-correctness03/artifacts'/(f.stem+f"-O{x['opt']}.wasm");after=out/before.name
 assert sha(before)==x['sha256']
 args=list(map(str,[exe,f"-O{x['opt']}",'--target','wasm','-o',after,f]));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120)
 rec={'source':x['source'],'source_sha256':sha(f),'opt':x['opt'],'parent':str(before),'parent_sha256':x['sha256'],'command':args,'exit':a.returncode,'stdout':a.stdout.decode(errors='replace'),'stderr':a.stderr.decode(errors='replace')}
 if not a.returncode:rec['sha256']=sha(after)
 rows.append(rec)
 if len(rows)%100==0 or a.returncode:(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
 assert not a.returncode,rec
 assert rec['sha256']==x['sha256'],rec
(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS',len(rows),'old modules byte-identical; current symbolic plan checked')
