from pathlib import Path
import subprocess,json
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');exe=p.parent/'build02/goose-tested';i=0;rows=[]
def run(args,ok=True):
 global i
 i+=1;args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120)
 (p/f'command-{i:03}.json').write_text(json.dumps(args)+'\n')
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/f'command-{i:03}.{k}').write_bytes(v)
 assert not ok or not a.returncode,(args,a.returncode,a.stderr)
 return a
f=p/'count.goose';f.write_text('struct S{n:u8}fn main(){var rows:S[u8]=['+','.join('S{7}' for _ in range(256))+'];print(rows.len);}\n')
for opt in (0,2):
 stem=p/f'count-O{opt}';c=stem.with_suffix('.c');native=stem.with_suffix('.native');module=stem.with_suffix('.wasm')
 run([exe,f'-O{opt}','--standalone','-o',c,f]);run(['cc',c,'-pthread','-lm','-ldl','-o',native]);a=run([native],False)
 assert a.returncode and b'array length exceeds stored prefix' in a.stderr,(a.returncode,a.stderr)
 a=run([exe,f'-O{opt}','--target','wasm','-o',module,f],False)
 assert a.returncode==1 and b'array length exceeds its stored prefix' in a.stderr and not module.exists(),a.stderr
 rows.append({'opt':opt,'status':'PASS native runtime range failure and Wasm compile-time range failure'})
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS 2 aggregate u8 count-256 range checks')
