from pathlib import Path
import subprocess,json,sys,hashlib
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;exe=p.parent/'build01/goose-tested';commands=[]
sys.path.insert(0,str(r/'test'))
def run(args,ok=True):
 args=list(map(str,args));name='command-'+str(len(commands));a=subprocess.run(args,cwd=r,capture_output=True,timeout=180)
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:(p/(name+'.'+ext)).write_bytes(data)
 commands.append({'name':name,'args':args,'exit':a.returncode});(p/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 if ok:assert not a.returncode,(name,args,a.stderr)
 return a
from wasm_fixed_negation_checks import check_images
import shutil
for name in ['owner','data_owner']:
 for opt in [0,2]:
  module='wasm_fixed_negation_'+name+f'-O{opt}.wasm';shutil.copy2(p.parent/'focused-owner01'/module,p/module)
print('PASS',check_images(run,'node','wasm-tools',p),'fixed negation image checks and controls')
