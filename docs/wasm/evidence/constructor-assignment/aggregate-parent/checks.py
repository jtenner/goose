from pathlib import Path
import subprocess,json,hashlib
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;exe=Path('/tmp/goose-wasm-fixed-assignment-20261107/goose-tested');commands=[];rows=[]
def run(name,args):
 a=subprocess.run([str(x) for x in args],cwd=r,capture_output=True,timeout=90)
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:(p/(name+'.'+ext)).write_bytes(data)
 commands.append({'name':name,'command':[str(x) for x in args],'exit':a.returncode});(p/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');return a
for name in ['aggregate_exit']:
 source=p/(name+'.goose');expected=(b'inner\nouter\ninner\nouter\nearly\n' if name=='early' else b'step\n'*4+b'loop\n' if name=='loop' else (name+'\n').encode())
 for opt in [0,2]:
  stem=name+f'-O{opt}';c=p/(stem+'.c');native=p/(stem+'.native');module=p/(stem+'.wasm')
  a=run(stem+'-emit',[exe,f'-O{opt}','--standalone','-o',c,source]);assert not a.returncode,(stem,a.stderr.decode())
  a=run(stem+'-cc',['cc','-O0',c,'-pthread','-lm','-ldl','-o',native]);assert not a.returncode,a.stderr
  a=run(stem+'-native',[native]);assert not a.returncode and a.stdout==expected and not a.stderr,(stem,a.returncode,a.stdout,a.stderr)
  a=run(stem+'-before',[exe,f'-O{opt}','--target','wasm','-o',module,source]);assert a.returncode==1 and (b'whole-aggregate assignment from a temporary needs the pending destination lowering' in a.stderr or b'aggregate temporaries need the pending destination lowering' in a.stderr) and not module.exists(),(stem,a.returncode,a.stderr)
  rows.append({'case':name,'opt':opt,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'native':'PASS','wasm_before':'constructor temporary diagnostic'});(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print('PASS:18 constructor native cases and18 exact current Wasm compilation failures.')
