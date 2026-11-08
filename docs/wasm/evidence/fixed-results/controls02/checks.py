from pathlib import Path
import subprocess,json,sys,hashlib
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;exe=p.parent/'build03/goose-tested';commands=[]
sys.path.insert(0,str(r/'test'))

def run(args,ok=True):
 args=list(map(str,args));name='command-'+str(len(commands));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120)
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:(p/(name+'.'+ext)).write_bytes(data)
 commands.append({'name':name,'args':args,'exit':a.returncode});(p/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 if ok:assert not a.returncode,(name,args,a.stderr)
 return a
from wasm_fixed_result_checks import check_guards,check_failure,check_target_failure
from wasm_aggregate_admission import check_admission
counts={'guards':check_guards(run,exe,'cc',p),'failure':check_failure(run,exe,'cc','node','wasm-tools',p),'target':check_target_failure(run,exe,'cc','node','wasm-tools',p),'aggregate_admission':check_admission(run,exe,'cc',p,'node','wasm-tools',Path('/tmp/goose-wasm-runtime-env/bin/python'))}
(p/'counts.json').write_text(json.dumps(counts,indent=2)+'\n');print('PASS',counts)
