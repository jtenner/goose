from pathlib import Path
import subprocess,json,hashlib
base=Path('/tmp/goose-wasm-fixed-arguments-20261107');p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');exe=Path('/tmp/goose-wasm-array-constructors-20261108/goose-tested');rows=[];commands=[]
for original in json.loads((base/'parent-first/results.json').read_text()):
 source=base/'parent-first'/(original['case']+'.goose');assert hashlib.sha256(source.read_bytes()).hexdigest()==original['source_sha256']
 stem=original['case']+f'-O{original["opt"]}';module=p/(stem+'.wasm');args=[str(exe),f'-O{original["opt"]}','--target','wasm','-o',str(module),str(source)]
 a=subprocess.run(args,cwd=r,capture_output=True,timeout=120)
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:(p/(stem+'.'+ext)).write_bytes(data)
 commands.append({'args':args,'exit':a.returncode});(p/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 assert a.returncode==1 and b'by-value aggregates need the pending destination lowering' in a.stderr and not module.exists(),a
 rows.append(dict(original,current_parent_guard=a.stderr.decode()));(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print('PASS',len(rows),'current parent argument guard checks; native records reused by source hash')
