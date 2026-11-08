from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');exe=p.parent/'build02/goose-tested';rows=[];i=0
reused=[]
for n,h in json.loads((p/'reused-artifact-hashes.json').read_text()).items():
 assert hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n
def run(args):
 global i
 args=list(map(str,args))
 old=p.parent/'focused01'
 for record in sorted(old.glob('command-*.json')):
  saved=json.loads(record.read_text())
  if saved==[x.replace(str(p),str(old)) for x in args]:
   stem=str(record.with_suffix(''));status=int(Path(stem+'.exit').read_text())
   if status:continue
   reused.append({'command':str(record),'sha256':hashlib.sha256(record.read_bytes()).hexdigest()})
   (p/'reused-commands.json').write_text(json.dumps(reused,indent=2)+'\n')
   return subprocess.CompletedProcess(args,status,Path(stem+'.stdout').read_bytes(),Path(stem+'.stderr').read_bytes())
 i+=1;a=subprocess.run(list(map(str,args)),cwd=r,capture_output=True,timeout=120)
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(f'command-{i:04}.'+k)).write_bytes(v)
 (p/f'command-{i:04}.json').write_text(json.dumps(list(map(str,args)))+'\n')
 assert not a.returncode,(args,a.returncode,a.stderr)
 return a
sources=sorted((r/'test/wasm').glob('wasm_compound_math_*.goose'))+sorted((r/'test/wasm').glob('wasm_negation_discard_*.goose'))
for f in sources:
 name=f.stem
 expected=(r/'test/expected'/(f.stem+'.out')).read_bytes()
 for opt in [0,2]:
  stem=name+f'-O{opt}';c=p/(stem+'.c');native=p/(stem+'.native');wasm=p/(stem+'.wasm')
  run([exe,f'-O{opt}','--standalone','-o',c,f]);run(['cc',c,'-pthread','-lm','-ldl','-o',native]);a=run([native]);assert a.stdout==expected,(name,a.stdout,expected)
  run([exe,f'-O{opt}','--target','wasm','-o',wasm,f]);run(['wasm-tools','validate',wasm])
  for host,args in [('node',['node',r/'scripts/run_wasm.mjs',wasm]),('wasmtime',['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',wasm])]:
   a=run(args);assert a.stdout==expected and not a.stderr,(name,host,a)
  mode='' if name in ['wasm_compound_math_data','wasm_compound_math_index_effect','wasm_compound_math_data_owner'] else 'no-data'
  a=run(['node',r/'test/wasm_multimemory.mjs',wasm,'1' if name=='wasm_compound_math_index_effect' else '0',mode]);assert a.stdout==expected and not a.stderr,(name,a)
  rows.append({'case':name,'opt':opt,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'wasm_sha256':hashlib.sha256(wasm.read_bytes()).hexdigest(),'status':'PASS'})
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS',len(rows),'native/Node/Wasmtime positive pairs and completed-owner checks')
