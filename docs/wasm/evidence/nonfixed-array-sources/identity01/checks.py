from pathlib import Path
import json,hashlib,subprocess
p=Path(__file__).parent;raw=p.parent;r=Path('/home/dev/Projects/goose-wasm-backend');old=Path('/tmp/goose-wasm-aggregate-prefix-20261108');exe=raw/'build01/goose-tested'
proof=json.loads((old/'full-correctness07/prefix-reuse.json').read_text());assert proof['status']=='PASS completed prefix verified; all later checks passed'
assert (old/'full-correctness07/check.exit').read_text().strip()=='0';source_hashes=json.loads((old/'validation-inputs.json').read_text());rows=[];commands=[]
assert hashlib.sha256(exe.read_bytes()).hexdigest()==json.loads((raw/'compiler-identity.json').read_text())['sha256']
for record in proof['fixtures']:
 source=r/record['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==source_hashes[record['source']]
 name=source.stem+f"-O{record['opt']}.wasm";before=old/'full-correctness07/artifacts'/name;after=p/name
 assert hashlib.sha256(before.read_bytes()).hexdigest()==record['sha256']
 args=list(map(str,[exe,f"-O{record['opt']}",'--target','wasm','-o',after,source]));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120)
 commands.append({'command':args,'exit':a.returncode,'stdout':a.stdout.decode(errors='replace'),'stderr':a.stderr.decode(errors='replace')})
 assert a.returncode==0,(args,a.stderr)
 h=hashlib.sha256(after.read_bytes()).hexdigest();rows.append({'source':record['source'],'opt':record['opt'],'parent':str(before),'parent_sha256':record['sha256'],'sha256':h,'status':'identical' if h==record['sha256'] else 'changed'})
 if len(rows)%100==0 or h!=record['sha256']:
  (p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');(p/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 assert rows[-1]['status']=='identical',rows[-1]
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');(p/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
assert len(rows)==1754,len(rows)
print('PASS',len(rows),'old fixture modules byte-identical to executed parent modules')
