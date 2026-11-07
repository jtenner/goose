from pathlib import Path
import sys,subprocess,json,hashlib,re,shutil
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;phase=sys.argv[1]
assert phase in ['parent','candidate']
out=p/phase;out.mkdir();manifest=[];rows=[]
exe=Path('/tmp/goose-wasm-array-places-20261107/build02/goose-tested') if phase=='parent' else p/'goose-tested'
def run(name,command, expected_exit=0):
 a=subprocess.run([str(v) for v in command],cwd=r,capture_output=True,timeout=180)
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:
  with (out/(name+'.'+ext)).open('xb') as f:f.write(data)
 manifest.append({'name':name,'command':[str(v) for v in command],'exit':a.returncode})
 (out/'commands-results.json').write_text(json.dumps(manifest,indent=2)+'\n')
 assert a.returncode==expected_exit,(name,a.returncode,a.stderr.decode(errors='replace'))
 return a
if phase=='parent':
 prior=p.parent/'build03';oldinputs=json.loads((prior/'input-hashes.json').read_text())
 for n in ['test/wasm/wasm_inline_ref_abi_thin.goose','test/expected/wasm_inline_ref_abi_thin.out']:
  assert hashlib.sha256((r/n).read_bytes()).hexdigest()==oldinputs[n],n
 reused=[x for x in json.loads((prior/'parent/case-results.json').read_text()) if x['source'].endswith('wasm_inline_ref_abi_thin.goose')]
 assert len(reused)==2
 for row in reused:
  name=Path(row['source']).stem+'-O'+str(row['opt']);base=prior/'parent'
  assert hashlib.sha256((base/(name+'.wasm')).read_bytes()).hexdigest()==row['module_sha256']
  for step in ['native-emit','native-build','native-run','emit','validate','node','wasmtime','wat']:
   assert (base/(name+'-'+step+'.exit')).read_text().strip()=='0',(name,step)
  expected=(r/'test/expected'/(Path(row['source']).stem+'.out')).read_bytes()
  for step in ['native-run','node','wasmtime']:
   assert (base/(name+'-'+step+'.stdout')).read_bytes()==expected
   assert not (base/(name+'-'+step+'.stderr')).read_bytes()
  image=json.loads((base/(name+'-instance')/'instance.json').read_text())
  for memory in image['memories']:
   assert hashlib.sha256((base/(name+'-instance')/(memory['name']+'.bin')).read_bytes()).hexdigest()==memory['sha256']
 copies=[]
 for f in (prior/'parent').glob('wasm_inline_ref_abi_thin-*'):
  target=out/f.name
  if f.is_dir():shutil.copytree(f,target)
  else:shutil.copy2(f,target)
  copies.append(str(f))
 for row in reused:row['reused_from']=str(prior/'parent');rows.append(row)
 (out/'reused-parent-results.json').write_text(json.dumps({'cases':reused,'original_artifacts':copies,'executed_again':False},indent=2)+'\n')
control=run('owner-field-admission',[exe,'-O0','--target','wasm','-o',out/'must-not-exist.wasm',p/'rejected-owner-field.goose'],expected_exit=1)
assert b'compound owner-reference fields need the pending destination lowering' in control.stderr
assert not (out/'must-not-exist.wasm').exists()
for stem in json.loads((p/'fixture-names.json').read_text()):
 if phase=='parent' and stem=='wasm_inline_ref_abi_thin':continue
 source=r/'test/wasm'/(stem+'.goose');expected=(r/'test/expected'/(stem+'.out')).read_bytes()
 for opt in [0,2]:
  name=stem+'-O'+str(opt);module=out/(name+'.wasm')
  if phase=='parent' and stem.startswith('wasm_inline_ref_abi_'):
   c=out/(name+'.c');native=out/(name+'.native')
   run(name+'-native-emit',[exe,'-O'+str(opt),'--standalone','-o',c,source])
   run(name+'-native-build',['cc','-O'+str(opt),c,'-pthread','-lm','-ldl','-o',native])
   a=run(name+'-native-run',[native]);assert a.stdout==expected and not a.stderr,(name,'native fixture expectation')
  run(name+'-emit',[exe,'-O'+str(opt),'--target','wasm','-o',module,source])
  run(name+'-validate',['wasm-tools','validate',module])
  a=run(name+'-node',['node',r/'test/wasm_reference_abi.mjs',module,out/(name+'-instance')]);assert a.stdout==expected and not a.stderr,(name,'Node expectation')
  b=run(name+'-wasmtime',['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',module]);assert b.stdout==expected and not b.stderr,(name,'Wasmtime expectation')
  snapshot=json.loads((out/(name+'-instance')/'instance.json').read_text());assert snapshot['completed'] and snapshot['pendingPrints']==0
  row={'source':str(source.relative_to(r)),'opt':opt,'module_bytes':module.stat().st_size,'module_sha256':hashlib.sha256(module.read_bytes()).hexdigest(),'memories':snapshot['memories'],'globals':snapshot['globals']}
  if phase=='parent' and stem.startswith('wasm_inline_ref_abi_'):
   text=run(name+'-wat',['wasm-tools','print',module]).stdout.decode()
   for fn in ['fixedref','limitedref']:
    found=[line for line in text.splitlines() if re.search(r'\(func \$'+fn+r'\.',line)]
    assert len(found)==1 and '(param i32) (result i32)' in found[0],(name,fn,found)
   row['parent_ordinary_array_reference_abi']='i32'
  if phase=='candidate':
   prior=json.loads((p/'parent'/(name+'-instance')/'instance.json').read_text());assert snapshot==prior,(name,'final memory/global metadata changed')
   for memory in snapshot['memories']:
    file=memory['name']+'.bin';assert (out/(name+'-instance')/file).read_bytes()==(p/'parent'/(name+'-instance')/file).read_bytes(),(name,file,'final memory changed')
   row['parent_memory_and_globals_exact']=True
   row['parent_module_identical']=module.read_bytes()==(p/'parent'/(name+'.wasm')).read_bytes()
   if stem=='wasm_inline_ref_abi_thin':assert row['parent_module_identical'],(name,'thin fixture module changed')
  rows.append(row);(out/'case-results.json').write_text(json.dumps(rows,indent=2)+'\n')
print(str(len(rows))+' '+phase+' O0/O2 cases passed in both engines, with completed memory snapshots.')
