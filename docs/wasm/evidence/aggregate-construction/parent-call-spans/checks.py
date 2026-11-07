from pathlib import Path
import subprocess,json,hashlib
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;exe=Path('/tmp/goose-wasm-constructor-assignment-20261107/build04/goose-tested');commands=[];rows=[]
cases=json.loads((p/'cases.json').read_text())

def run(stem,label,args):
 a=subprocess.run(list(map(str,args)),cwd=r,capture_output=True,timeout=90)
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:(p/(stem+'-'+label+'.'+ext)).write_bytes(data)
 commands.append({'name':stem+'-'+label,'args':list(map(str,args)),'exit':a.returncode});(p/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');return a
for name,text in cases.items():
 source=p/(name+'.goose');source.write_text(text)
 for opt in [0,2]:
  stem=name+f'-O{opt}';c=p/(stem+'.c');native=p/(stem+'.native');module=p/(stem+'.wasm')
  for label,args in [('emit',[exe,f'-O{opt}','--standalone','-o',c,source]),('cc',['cc',c,'-pthread','-lm','-ldl','-o',native]),('native',[native])]:
   a=run(stem,label,args);assert not a.returncode,(name,label,a.stderr)
   if label=='native':assert a.stdout==(name+'\n').encode() and not a.stderr,(name,a.stdout,a.stderr)
  a=run(stem,'before',[exe,f'-O{opt}','--target','wasm','-o',module,source]);assert a.returncode==1 and (b'aggregate array defaults' in a.stderr or b'aggregate array fills' in a.stderr),a.stderr
  rows.append({'case':name,'opt':opt,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'native':'PASS','wasm_before':a.stderr.decode()});(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print('PASS:',len(rows),'native cases and exact current Wasm fill/default failures.')
