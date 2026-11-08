from pathlib import Path
import subprocess,sys
sys.path.insert(0,str(Path('/home/dev/Projects/goose-wasm-backend/test')))
from wasm_array_expression_checks import check_defer,check_inline,check_guards
p=Path(__file__).parent;i=0
def run(args,ok=True):
 global i
 i+=1;a=subprocess.run(list(map(str,args)),capture_output=True)
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(f'command-{i:04}.'+k)).write_bytes(v)
 assert not ok or a.returncode==0,(args,a.returncode,a.stderr)
 return a
out=p.parent/'focused01'
print('PASS',check_defer(run,'node','wasm-tools',out)+check_inline(run,'node','wasm-tools',p.parent/'focused02')+check_guards(run,p.parent/'build01/goose-tested','cc',out),'image/control/guard checks')
