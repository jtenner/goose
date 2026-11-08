from pathlib import Path
import subprocess,json,sys,hashlib
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;exe=p.parent/'build01/goose-tested';commands=[]
sys.path.insert(0,str(r/'test'))

def run(args,ok=True):
 args=list(map(str,args));name='command-'+str(len(commands));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120)
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:(p/(name+'.'+ext)).write_bytes(data)
 commands.append({'name':name,'args':args,'exit':a.returncode});(p/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 if ok:assert not a.returncode,(name,args,a.stderr)
 return a
from wasm_array_result_checks import check_images
for opt in [0,2]:
 source=r/'test/wasm/wasm_array_result_owner.goose';run([exe,f'-O{opt}','--target','wasm','-o',p/f'wasm_array_result_owner-O{opt}.wasm',source])
count=check_images(run,'node','wasm-tools',p)
(p/'counts.json').write_text(json.dumps({'image_groups':count},indent=2)+'\n');print('PASS',count,'array result image groups')
