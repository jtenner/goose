from pathlib import Path
import subprocess,json,sys
sys.dont_write_bytecode=True
p=Path(__file__).parent;root=p.parent;r=Path('/home/dev/Projects/goose-wasm-backend');exe=p/'goose-tested';rows=[];failed=[]
sys.path.insert(0,str(r/'test'));from wasm_backend import function_local_counts
stats=[]
def run(name,args):
 args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=180)
 for ext,d in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]:
  with (p/(name+'.'+ext)).open('xb') as f:f.write(d)
 rows.append({'name':name,'command':args,'exit':a.returncode});(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');return a
def check(name,source,opt,expected,owner=False):
 w=p/(name+'.wasm');a=run(name+'-emit',[exe,'-O'+str(opt),'--target','wasm','-o',w,source])
 if a.returncode:failed.append(name+' emit');return
 a=run(name+'-validate',['wasm-tools','validate',w])
 if a.returncode:failed.append(name+' validate');return
 for runtime,command in [('node',['node',r/'scripts/run_wasm.mjs',w]),('wasmtime',['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',w])]:
  a=run(name+'-'+runtime,command)
  if a.returncode or a.stdout!=expected or a.stderr:failed.append(name+' '+runtime)
 if owner:
  mode='frame-growth' if name.startswith('wasm_aggregate_array_cleanup') else '' if name.startswith('wasm_aggregate_array_packed') else 'no-data'
  a=run(name+'-owner',['node',r/'test/wasm_multimemory.mjs',w,'0',mode])
  if a.returncode or a.stdout!=expected or a.stderr:failed.append(name+' owner')
 return w
for case,entry in json.loads((root/'promoted.json').read_text()).items():
 for opt in [0,2]:check(case+'-O'+str(opt),r/'test/wasm'/(case+'.goose'),opt,Path(entry['expected']).read_bytes(),True)
for opt in [0,2]:check('global-effects-O'+str(opt),p/'global-effects.goose',opt,(p/('native-global-effects-O'+str(opt)+'-run.stdout')).read_bytes())
for case,(_,reasons) in json.loads((root/'gate-cases.json').read_text()).items():
 for opt in [0,2]:
  name='gate-'+case+'-O'+str(opt);w=p/(name+'.wasm');a=run(name,[exe,'-O'+str(opt),'--target','wasm','-o',w,p/(case+'.goose')])
  if not a.returncode or w.exists() or not any(reason.encode() in a.stderr for reason in reasons):failed.append(name+' admission')
for kind in ['named','literal']:
 observed=[]
 for length in [32,256]:
  items=', '.join(['s']*length if kind=='named' else ['S { x: '+str(i%251)+' }' for i in range(length)])
  source=p/(kind+'-'+str(length)+'.goose');source.write_text('struct S { x: i64 }\nfn main() { '+('var s: S = S { x: 7 }; ' if kind=='named' else '')+'var a: S['+str(length)+'] = ['+items+']; print(a.len, ",", a['+str(length-1)+'].x); }\n')
  expected=(str(length)+','+str(7 if kind=='named' else (length-1)%251)+'\n').encode()
  for opt in [0,2]:
   name=kind+'-'+str(length)+'-O'+str(opt);w=check(name,source,opt,expected)
   if w:
    counts=function_local_counts(w.read_bytes());stats.append({'name':name,'bytes':w.stat().st_size,'locals':counts});observed.append(counts)
 if len(observed)!=4 or not all(x==observed[0] for x in observed) or max(observed[0])>64:failed.append(kind+' local scaling')
(p/'footprint.json').write_text(json.dumps(stats,indent=2)+'\n');(p/'summary.json').write_text(json.dumps({'failed':failed,'commands':len(rows)},indent=2)+'\n');print(json.dumps({'failed':failed,'commands':len(rows)}));sys.exit(bool(failed))
