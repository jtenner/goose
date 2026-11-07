from pathlib import Path
import ast,subprocess,json,hashlib
r=Path.cwd();p=Path('/tmp/goose-wasm-runtime-limited-20261107/review-checks');exe=p.parent/'goose-tested';rows=[]
source=r/'test/wasm_backend.py';tree=ast.parse(source.read_text())
node=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='failures' for t in n.targets))
cases={name:(body,reason) for name,body,reason in ast.literal_eval(node.value)}
def run(name,args,success=True):
 args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=90)
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(name+'.'+ext)).write_bytes(data)
 rows.append({'name':name,'command':args,'exit':a.returncode});(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
 if success:assert a.returncode==0,(name,a.stderr)
 return a
for case in ['runtime-index','runtime-negative','runtime-large']:
 body,reason=cases[case];s=p/(case+'.goose');s.write_text(('var failure_index: i64 = 1;\n' if case=='runtime-index' else '')+'fn main() { '+body+' }\n')
 for opt in [0,2]:
  n=case+'-O'+str(opt);c=p/(n+'.c');native=p/(n+'.native');w=p/(n+'.wasm')
  run(n+'-native-emit',[exe,'-O'+str(opt),'--standalone','-o',c,s]);run(n+'-native-build',['cc','-O0',c,'-pthread','-lm','-ldl','-o',native]);a=run(n+'-native',[native],False)
  native_reason=b'invalid capacity' if case!='runtime-index' else b'out of bounds';assert a.returncode and native_reason in a.stderr and not a.stdout,(n,a.stderr)
  run(n+'-emit',[exe,'-O'+str(opt),'--target','wasm','-o',w,s]);run(n+'-validate',['wasm-tools','validate',w])
  for host,args in [('node',['node',r/'scripts/run_wasm.mjs',w]),('wasmtime',['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',w])]:
   a=run(n+'-'+host,args,False);assert a.returncode and reason in a.stderr and not a.stdout,(n,host,a.stderr)
# A valid derived control uses the capacity field only for the index check.
# Keep push's length load unchanged. All code/section lengths stay unchanged.
w=p/'runtime-index-O0.wasm';data=bytearray(w.read_bytes());pos=8;span=None
def read(pos):
 n=shift=0
 while True:
  b=data[pos];pos+=1;n|=(b&127)<<shift
  if not b&128:return n,pos
  shift+=7
while pos<len(data):
 kind=data[pos];length,start=read(pos+1);end=start+length
 if kind==10:span=(start,end)
 pos=end
assert span
pattern=bytes([0x35,0x40,1,4]);positions=[];pos=span[0]
while True:
 pos=data.find(pattern,pos,span[1])
 if pos<0:break
 positions.append(pos);pos+=len(pattern)
assert len(positions)==2,positions
data[positions[-1]+3]=0;control=p/'wrong-capacity-bound.wasm';control.write_bytes(data)
run('wrong-capacity-bound-validate',['wasm-tools','validate',control])
for host,args in [('node',['node',r/'scripts/run_wasm.mjs',control]),('wasmtime',['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',control])]:
 a=run('wrong-capacity-bound-'+host,args);assert a.stdout==b'bad=0\n' and not a.stderr,(host,a.stdout,a.stderr)
(p/'identity.json').write_text(json.dumps({'compiler_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'final_harness_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'control_source':'runtime-index-O0.wasm','changed_byte':positions[-1]+3,'correct_field_offset':4,'wrong_field_offset':0,'control_sha256':hashlib.sha256(data).hexdigest()},indent=2)+'\n')
print('Six exact-error cases pass; valid wrong-capacity-bound control returns bad=0 in both engines and is rejected by the strengthened expectation.')
