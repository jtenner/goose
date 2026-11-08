from pathlib import Path
import subprocess,sys,json,traceback
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;sys.path.insert(0,str(r/'test'));exe=p.parent/'build02/goose-tested';commands=[]
def run(args,ok=True):
 a=subprocess.run(list(map(str,args)),cwd=r,capture_output=True,timeout=120);name='command-'+str(len(commands))
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:(p/(name+'.'+ext)).write_bytes(data)
 commands.append({'args':list(map(str,args)),'exit':a.returncode});(p/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 if ok:assert not a.returncode,a.stderr
 return a
import wasm_struct_admission,wasm_enum_admission
counts={}
counts['struct']=wasm_struct_admission.check_admission(run,exe,'node','wasm-tools','/tmp/goose-wasm-runtime-env/bin/python',p)
counts['enum']=wasm_enum_admission.check_admission(run,exe,'cc',p,'node','wasm-tools','/tmp/goose-wasm-runtime-env/bin/python')
(p/'counts.json').write_text(json.dumps(counts,indent=2)+'\n');print('PASS',counts)
