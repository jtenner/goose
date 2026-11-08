from pathlib import Path
import subprocess,json
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;exe=Path('/tmp/goose-wasm-array-assignment-20261107/goose-tested');rows=[];commands=[]
cases={'scalar':'fn main(){var a:u16[..3]=default<u16[2]>();print(a.len);}\n','nominal':'struct S{n:i64=7}\nfn main(){var a:S[..3]=default<S[2]>();print(a.len);}\n','field':'struct S{n:i64=7}\nstruct H{rows:S[..3]}\nfn main(){var h:H=H{rows:default<S[2]>()};print(h.rows.len);}\n'}
def run(name,args):
 a=subprocess.run(list(map(str,args)),cwd=r,capture_output=True,timeout=120)
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:(p/(name+'.'+ext)).write_bytes(data)
 commands.append({'name':name,'args':list(map(str,args)),'exit':a.returncode});(p/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');return a
for name,text in cases.items():
 source=p/(name+'.goose');source.write_text(text)
 for opt in [0,2]:
  stem=name+f'-O{opt}';c=p/(stem+'.c');native=p/(stem+'.native');module=p/(stem+'.wasm')
  for label,args in [('emit',[exe,f'-O{opt}','--standalone','-o',c,source]),('cc',['cc',c,'-pthread','-lm','-ldl','-o',native]),('native',[native])]:
   a=run(stem+'-'+label,args);assert not a.returncode,(name,label,a.stderr)
   if label=='native':assert a.stdout==b'2\n' and not a.stderr,a
  a=run(stem+'-wasm',[exe,f'-O{opt}','--target','wasm','-o',module,source]);entry={'case':name,'opt':opt,'native_stdout':'2\n','wasm_compile_exit':a.returncode,'wasm_error':a.stderr.decode()}
  if not a.returncode:
   a=run(stem+'-validate',['wasm-tools','validate',module]);assert not a.returncode,a.stderr
   a=run(stem+'-node',['node',r/'scripts/run_wasm.mjs',module]);entry.update(candidate_exit=a.returncode,candidate_stdout=a.stdout.decode(),candidate_stderr=a.stderr.decode())
  rows.append(entry);(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(entry)
