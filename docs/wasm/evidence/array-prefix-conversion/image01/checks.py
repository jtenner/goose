from pathlib import Path
import subprocess,sys
sys.path.insert(0,str(Path('/home/dev/Projects/goose-wasm-backend/test')))
from wasm_array_prefix_conversion_checks import check_images,check_failures,check_pending_aggregate
p=Path(__file__).parent;i=0
def run(args,ok=True):
 global i
 i+=1;a=subprocess.run(list(map(str,args)),capture_output=True)
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+"\n".encode())]: (p/(f'command-{i:04}.'+k)).write_bytes(v)
 assert not ok or a.returncode==0,(args,a.returncode,a.stderr)
 return a
out=p.parent/'focused02';exe=p.parent/'build01/goose-tested'
print('PASS',check_images(run,'node','wasm-tools',out)+check_failures(run,exe,'cc','node','wasm-tools','/tmp/goose-wasm-runtime-env/bin/python',out)+check_pending_aggregate(run,exe,'cc',out),'image/control/guard checks')
