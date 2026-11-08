from pathlib import Path
import subprocess,json,hashlib
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;exe=Path('/tmp/goose-wasm-fixed-negation-20261108/build01/goose-tested');rows=[]
def run(name,args):
 a=subprocess.run(list(map(str,args)),cwd=r,capture_output=True,timeout=120)
 for ext,b in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]:(p/(name+'.'+ext)).write_bytes(b)
 return a
for name,text in json.loads((p/'cases.json').read_text()).items():
 source=p/(name+'.goose');source.write_text(text)
 for opt in [0,2]:
  stem=name+f'-O{opt}';c=p/(stem+'.c');native=p/(stem+'.native')
  a=run(stem+'-emit',[exe,f'-O{opt}','--standalone','-o',c,source]);assert not a.returncode,a.stderr
  a=run(stem+'-cc',['cc',c,'-pthread','-lm','-ldl','-o',native]);assert not a.returncode,a.stderr
  a=run(stem+'-before',[native]);assert a.returncode!=0 and b'assert failed' in a.stderr,(name,a)
  rows.append({'case':name,'opt':opt,'exit':a.returncode,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'c_sha256':hashlib.sha256(c.read_bytes()).hexdigest(),'expected':name+'\n','actual':a.stdout.decode(),'reason':a.stderr.decode()})
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS recorded',len(rows),'native failing-first cases')
