from pathlib import Path
import sys,subprocess,json
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;sys.path.insert(0,str(r/'test'))
from wasm_aggregate_checks import check_reference_abi
rows=[]
def run(command):
 a=subprocess.run([str(v) for v in command],cwd=r,capture_output=True,timeout=90);n=len(rows)
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:(p/('shape-'+str(n)+'.'+ext)).write_bytes(data)
 rows.append({'command':[str(v) for v in command],'exit':a.returncode});(p/'shape-commands.json').write_text(json.dumps(rows,indent=2)+'\n')
 assert a.returncode==0,(command,a.stderr)
 return a
count=check_reference_abi(run,'wasm-tools',p/'candidate');assert count==26,count
print(str(count)+' thin/packed reference signature checks passed; true growable header stays i32.')
