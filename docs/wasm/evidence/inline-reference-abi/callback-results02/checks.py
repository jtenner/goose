from pathlib import Path
import subprocess,json,hashlib,re
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');commands=[];rows=[]
def run(name,args):
 a=subprocess.run([str(x) for x in args],cwd=r,capture_output=True,timeout=120)
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:(p/(name+'.'+ext)).write_bytes(data)
 commands.append({'name':name,'command':[str(x) for x in args],'exit':a.returncode});(p/'commands-results.json').write_text(json.dumps(commands,indent=2)+'\n')
 assert a.returncode==0,(name,a.returncode,a.stderr.decode(errors='replace'))
 return a
for phase,exe in [('parent',Path('/tmp/goose-wasm-array-places-20261107/build02/goose-tested')),('candidate',p.parent/'build04/goose-tested')]:
 for mode in ['thin','packed']:
  stem='wasm_inline_ref_callback_'+mode;source=r/'test/wasm'/(stem+'.goose');expected=(r/'test/expected'/(stem+'.out')).read_bytes()
  for opt in [0,2]:
   name=phase+'-'+stem+'-O'+str(opt);module=p/(name+'.wasm')
   if phase=='parent':
    c=p/(name+'.c');native=p/(name+'.native')
    run(name+'-native-emit',[exe,'-O'+str(opt),'--standalone','-o',c,source]);run(name+'-native-build',['cc','-O'+str(opt),c,'-pthread','-lm','-ldl','-o',native]);a=run(name+'-native-run',[native]);assert a.stdout==expected and not a.stderr
   run(name+'-emit',[exe,'-O'+str(opt),'--target','wasm','-o',module,source]);run(name+'-validate',['wasm-tools','validate',module])
   a=run(name+'-node',['node',r/'test/wasm_reference_abi.mjs',module,p/(name+'-instance')]);assert a.stdout==expected and not a.stderr
   a=run(name+'-wasmtime',['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',module]);assert a.stdout==expected and not a.stderr
   state=json.loads((p/(name+'-instance')/'instance.json').read_text());assert state['completed'] and state['completionCalls']==1 and state['pendingPrints']==state['pendingSnapshots']==0
   text=run(name+'-wat',['wasm-tools','print',module]).stdout.decode();rep='i64' if phase=='candidate' and mode=='packed' else 'i32'
   for function in ['relayFixed','relayMaybeFixed']:
    found=[x for x in text.splitlines() if re.search(r'\(func \$'+function+r'\.',x)];assert len(found)==1 and f'(param {rep}) (result {rep})' in found[0],(name,function,found)
   if phase=='candidate':
    old='parent-'+stem+'-O'+str(opt);prior=json.loads((p/(old+'-instance')/'instance.json').read_text());assert state==prior
    for memory in state['memories']:assert (p/(name+'-instance')/(memory['name']+'.bin')).read_bytes()==(p/(old+'-instance')/(memory['name']+'.bin')).read_bytes()
    if mode=='thin':assert module.read_bytes()==(p/(old+'.wasm')).read_bytes()
   rows.append({'phase':phase,'mode':mode,'opt':opt,'module_sha256':hashlib.sha256(module.read_bytes()).hexdigest(),'state':state,'reference_signature':rep});(p/'case-results.json').write_text(json.dumps(rows,indent=2)+'\n')
assert len(rows)==8
print('8callback-reference cases passed in both engines;4native references,4exact memory pairs,thin module identity and result signatures pass.')
