from pathlib import Path
import sys,subprocess,json,shutil,hashlib
raw=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');out=raw/'images02';out.mkdir(exist_ok=True);sys.path.insert(0,str(r/'test'));from wasm_callback_borrow_checks import check_images,check_guards
serial=0
for name in ['owner','growth']:
 for opt in [0,2]:
  f=raw/'focused01'/f'wasm_callback_borrow_{name}-O{opt}.wasm';shutil.copy2(f,out/f.name)
def run(args,ok=True):
 global serial
 serial+=1;args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120);base=out/f'command-{serial:04}';base.with_suffix('.json').write_text(json.dumps(args)+'\n');base.with_suffix('.stdout').write_bytes(a.stdout);base.with_suffix('.stderr').write_bytes(a.stderr);base.with_suffix('.exit').write_text(str(a.returncode)+'\n')
 if ok:assert not a.returncode,(args,a.returncode,a.stderr)
 return a
n=check_images(run,'node','wasm-tools',out);assert n==16,n;print('PASS',n,'complete Memory 0 owner/growth images and specific fault controls')
