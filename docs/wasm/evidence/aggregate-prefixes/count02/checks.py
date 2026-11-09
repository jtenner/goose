from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');exe=p.parent/'build02/goose-tested';f=p.parent/'count01/count.goose';i=0
assert f.read_text().count('S{7}')==256
for opt in (0,2):
 for kind,flags,ext in [('native',['--standalone'],'.c'),('wasm',['--target','wasm'],'.wasm')]:
  i+=1;out=p/(kind+str(opt)+ext);args=list(map(str,[exe,f'-O{opt}',*flags,'-o',out,f]));a=subprocess.run(args,cwd=r,capture_output=True)
  (p/f'command-{i:03}.json').write_text(json.dumps(args)+'\n')
  for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/f'command-{i:03}.{k}').write_bytes(v)
  assert a.returncode==1 and b'array length 256 exceeds storage range of S[u8]' in a.stderr and not out.exists(),(kind,opt,a.returncode,a.stderr)
(p/'results.json').write_text(json.dumps({'status':'PASS','source_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'frontend_range_rejections':4},indent=2)+'\n')
print('PASS 4 exact frontend u8 count-256 rejections, native and Wasm paths at O0/O2')
