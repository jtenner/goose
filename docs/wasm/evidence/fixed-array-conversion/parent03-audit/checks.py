from pathlib import Path
import json,hashlib,subprocess
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');old=p.parent/'parent01';exe=Path('/tmp/goose-wasm-zero-call-20261108/build01/goose-tested');rows=[]
for row in json.loads((old/'results.json').read_text()):
 name=row['case'];source=old/(name+'.goose');assert row['native']=='PASS' and hashlib.sha256(source.read_bytes()).hexdigest()==row['source_sha256']
 for kind in ['emit','cc','native']:assert (old/(name+'-'+kind+'.exit')).read_text().strip()=='0'
 assert (old/(name+'-native.stdout')).read_bytes()==name.encode()+b'\n'
 module=p/(name+'.wasm');args=[exe,'-O0','--target','wasm','-o',module,source]
 a=subprocess.run(list(map(str,args)),cwd=r,capture_output=True,timeout=120)
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(name+'.'+k)).write_bytes(v)
 assert a.returncode==1 and not module.exists(),(name,a)
 rows.append({'case':name,'source_sha256':row['source_sha256'],'wasm_reason':a.stderr.decode(),'native_reused':str(old/(name+'-native.json'))})
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS',len(rows),'current-parent Wasm failures with verified native result reuse')
