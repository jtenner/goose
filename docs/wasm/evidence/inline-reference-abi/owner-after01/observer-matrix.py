from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');base=p.parent/'build04';rows=[];commands=[]
for phase in ['parent','candidate']:
 for original in json.loads((base/phase/'case-results.json').read_text()):
  stem=Path(original['source']).stem+'-O'+str(original['opt']);module=base/phase/(stem+'.wasm');assert hashlib.sha256(module.read_bytes()).hexdigest()==original['module_sha256'];out=p/phase/(stem+'-instance');out.parent.mkdir(exist_ok=True)
  command=['node',str(r/'test/wasm_reference_abi.mjs'),str(module),str(out)];a=subprocess.run(command,cwd=r,capture_output=True,timeout=120)
  for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:(p/(phase+'-'+stem+'.'+ext)).write_bytes(data)
  commands.append({'command':command,'exit':a.returncode});(p/'matrix-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
  assert a.returncode==0,(phase,stem,a.stderr);assert not a.stderr;assert a.stdout==(r/'test/expected'/(Path(original['source']).stem+'.out')).read_bytes()
  state=json.loads((out/'instance.json').read_text());assert state['completed'] and state['completionCalls']==1 and state['pendingPrints']==0 and state['pendingSnapshots']==0
  for memory in state['memories']:
   data=(out/(memory['name']+'.bin')).read_bytes();assert hashlib.sha256(data).hexdigest()==memory['sha256'];assert data==(base/phase/(stem+'-instance')/(memory['name']+'.bin')).read_bytes()
  assert state['globals']==[]
  if phase=='candidate':
   prior=json.loads((p/'parent'/(stem+'-instance')/'instance.json').read_text());assert state==prior
  rows.append({'phase':phase,'source':original['source'],'opt':original['opt'],'observed':state,'matches_original_memory':True});(p/'matrix-results.json').write_text(json.dumps(rows,indent=2)+'\n')
assert len(rows)==64
print('64 corrected pre-cleanup owner observations passed; all memory images match the original records and32parent/candidate pairs.')
