from pathlib import Path
import subprocess,json
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');i=0
def run(args,ok=True):
 global i
 i+=1;args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True)
 (p/f'command-{i:03}.json').write_text(json.dumps(args)+'\n')
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(f'command-{i:03}.'+k)).write_bytes(v)
 assert not ok or a.returncode==0,(args,a.returncode,a.stderr)
 return a
parent='/tmp/goose-wasm-limited-array-layout-20261108/build02/goose-tested';candidate=p.parent/'build01/goose-tested';f=p/'case.goose'
run([parent,'--standalone','-o',p/'case.c',f]);run(['cc',p/'case.c','-pthread','-lm','-ldl','-o',p/'case.native']);a=run([p/'case.native']);assert a.stdout==b'runtime256\n' and not a.stderr
run([candidate,'--target','wasm','-o',p/'case.wasm',f]);run(['wasm-tools','validate',p/'case.wasm']);a=run(['node',r/'scripts/run_wasm.mjs',p/'case.wasm']);assert a.stdout==b'runtime256\n' and not a.stderr
