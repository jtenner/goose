from pathlib import Path
import subprocess,sys
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;sys.path.insert(0,str(r/'test'))
from wasm_fixed_binary_checks import emit
i=0
def run(args,ok=True):
 global i
 i+=1;a=subprocess.run(list(map(str,args)),capture_output=True)
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/f'command-{i:03}.{k}').write_bytes(v)
 assert not ok or not a.returncode,(args,a.stderr)
 return a
text=run(['wasm-tools','print',p.parent/'dynamic-parent01/dynamic.wasm']).stdout.decode();module=emit(run,'wasm-tools',p,'dirty-parent',text,3)
a=run(['node',r/'test/wasm_aggregate_prefix_dynamic.mjs',module],False)
assert a.returncode==1 and a.stdout==b'before\n' and b'aggregate dynamic data image differs' in a.stderr,a.stderr
print('PASS accepted-parent dirty-image failure reproduced at first completed constructor')
