from pathlib import Path
import subprocess,json,hashlib,re,sys
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');exe=p.parent/'build05/goose-tested';parent=Path('/tmp/goose-wasm-inline-ref-abi-20261107/build04/goose-tested');commands=[];records=[]
sys.path.insert(0,str(r/'test'));from wasm_data_aggregate_controls import derive

def run(name,args,ok=True):
 a=subprocess.run([str(x) for x in args],cwd=r,capture_output=True,timeout=120)
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:(p/(name+'.'+ext)).write_bytes(data)
 commands.append({'name':name,'args':[str(x) for x in args],'exit':a.returncode});(p/'commands-results.json').write_text(json.dumps(commands,indent=2)+'\n')
 if ok:assert a.returncode==0,(name,a.stderr.decode(errors='replace'))
 return a
sources={'cleanup':r/'test/wasm/wasm_data_aggregate_cleanup.goose','growth':p/'growth.goose','overflow':p/'overflow.goose'}
expected={'cleanup':b'data-cleanup=ok\n','growth':b'ready\nchild\nchild\ndone\n','overflow':b'ready\ndone\n'}
errors=[]
for kind,source in sources.items():
 for opt in [0,2]:
  name=f'{kind}-O{opt}';a=run(name+'-native-emit',[parent,'-O'+str(opt),'--standalone','-o',p/(name+'.c'),source],False)
  if a.returncode:errors.append({'name':name,'stderr':a.stderr.decode(errors='replace')})
(p/'native-preflight.json').write_text(json.dumps({'errors':errors,'cases':6},indent=2)+'\n');assert not errors,errors

def reservation(name,module,mode,line=None):
 for engine,command in [('node',['node',r/'test/wasm_data_aggregate_reservation.mjs']),('wasmtime',['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasm_data_aggregate_reservation.py'])]:
  result=p/(name+'-'+engine+'.json');args=[*command,module,mode,result]
  if line is not None:args.append(str(line))
  a=run(name+'-'+engine,args);want=expected['growth'] if mode=='growth-healthy' else b'allocation-control=ok\n';assert a.stdout==want and not a.stderr,(name,engine,a.stdout,a.stderr)
  assert json.loads(result.read_text())['allChecks']=='PASS'
for kind,source in sources.items():
 for opt in [0,2]:
  name=f'{kind}-O{opt}';native=p/(name+'.native');module=p/(name+'.wasm')
  run(name+'-native-build',['cc','-O0',p/(name+'.c'),'-pthread','-lm','-ldl','-o',native]);a=run(name+'-native-run',[native]);assert a.stdout==expected[kind] and not a.stderr
  run(name+'-emit',[exe,'-O'+str(opt),'--target','wasm','-o',module,source]);run(name+'-validate',['wasm-tools','validate',module])
  if kind=='growth':
   healthy=p/(name+'-tops.wasm');healthy.write_bytes(derive(module.read_bytes()));run(name+'-tops-validate',['wasm-tools','validate',healthy]);reservation(name+'-dirty',healthy,'growth-healthy')
   limited=p/(name+'-limit.wasm');limited.write_bytes(derive(module.read_bytes(),True));run(name+'-limit-validate',['wasm-tools','validate',limited]);reservation(name+'-failure',limited,'growth-failure')
   if opt==0:
    text=run(name+'-wat',['wasm-tools','print',healthy]).stdout.decode();pattern=r'\bmemory\.fill\s+1\b';assert len(re.findall(pattern,text))==2
    damaged=p/'wrong-zero.wat';damaged.write_text(re.sub(pattern,'memory.fill',text,count=1));bad=damaged.with_suffix('.wasm');run('wrong-zero-parse',['wasm-tools','parse',damaged,'-o',bad]);run('wrong-zero-validate',['wasm-tools','validate',bad]);line=next(i for i,s in enumerate(source.read_text().splitlines(),1) if 'assert(rows[0].bytes[39999]' in s);reservation('wrong-zero',bad,'growth-bad-zero',line)
  else:
   a=run(name+'-node',['node',r/'test/wasm_multimemory.mjs',module,'1' if kind=='overflow' else '0']);assert a.stdout==expected[kind] and not a.stderr
   a=run(name+'-wasmtime',['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',module]);assert a.stdout==expected[kind] and not a.stderr
   if kind=='overflow':
    control=p/(name+'-tops.wasm');control.write_bytes(derive(module.read_bytes()));run(name+'-tops-validate',['wasm-tools','validate',control]);reservation(name+'-failure',control,'overflow')
  records.append({'kind':kind,'opt':opt,'status':'PASS','module_sha256':hashlib.sha256(module.read_bytes()).hexdigest()});(p/'results.json').write_text(json.dumps(records,indent=2)+'\n')
source=p/'wrong-order.goose';text=sources['cleanup'].read_text();assert text.count('[inner(1), inner(2)]')==1;source.write_text(text.replace('[inner(1), inner(2)]','[inner(2), inner(1)]'))
line=next(i for i,s in enumerate(text.splitlines(),1) if 'assert(trace == 1020305060709)' in s)
for opt in [0,2]:
 name=f'wrong-order-O{opt}';c=p/(name+'.c');native=p/(name+'.native');module=p/(name+'.wasm')
 run(name+'-native-emit',[parent,'-O'+str(opt),'--standalone','-o',c,source]);run(name+'-native-build',['cc','-O0',c,'-pthread','-lm','-ldl','-o',native]);run(name+'-emit',[exe,'-O'+str(opt),'--target','wasm','-o',module,source]);run(name+'-validate',['wasm-tools','validate',module])
 for engine,command in [('native',[native]),('node',['node',r/'scripts/run_wasm.mjs',module]),('wasmtime',['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',module])]:
  a=run(name+'-'+engine,command,False);assert a.returncode and b'assert' in a.stderr.lower() and f'{source}:{line}'.encode() in a.stderr and not a.stdout,(name,engine,a.stdout,a.stderr)
print('6healthy native references/12engine cases,8reservation controls,2wrong-zero controls and6wrong-order controls PASS.')
