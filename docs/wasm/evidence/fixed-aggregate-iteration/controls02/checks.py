from pathlib import Path
import re,json,subprocess,hashlib,sys
p=Path(__file__).parent;root=p.parent;r=Path('/home/dev/Projects/goose-wasm-backend');prior=root/'controls01';rows=[]
assert hashlib.sha256((root/'build01/goose-tested').read_bytes()).hexdigest()=='c9519e59d47ea996b84d249fee688704bfab0ed49cf5c1ef844e7daf3bdd60d2'

def run(name,args,expected=0):
 args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120)
 for ext,value in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]:
  with (p/(name+'.'+ext)).open('xb') as f:f.write(value)
 rows.append({'name':name,'command':args,'exit':a.returncode});(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
 assert (a.returncode==0)==(expected==0),(name,a.stderr.decode(errors='replace'));return a

def module(name,text):
 wat=p/(name+'.wat');wat.write_text(text);w=wat.with_suffix('.wasm');run(name+'-parse',['wasm-tools','parse',wat,'-o',w]);run(name+'-validate',['wasm-tools','validate',w]);return w

def failure(name,w,source,assertion,stdout=b''):
 line=next(i for i,s in enumerate(source.read_text().splitlines(),1) if assertion in s)
 for engine,args in [('node',['node',r/'scripts/run_wasm.mjs',w]),('wasmtime',['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',w])]:
  a=run(name+'-'+engine,args,1);assert b'assert failed' in a.stderr and f'{source}:{line}'.encode() in a.stderr,(name,a.stderr);assert a.stdout==stdout,(name,'wrong failure ordering',a.stdout)

for opt in [0,2]:
 stem='O'+str(opt)
 # Only the failed live-owner adapter is repeated, with unchanged guest modules.
 a=run(stem+'-cleanup-live-owner',['node',r/'test/wasm_iteration_owner.mjs',prior/('checkpoint-'+stem+'-owner.wasm'),'cleanup'])
 assert a.stdout==(prior/('checkpoint-'+stem+'-native-run.stdout')).read_bytes() and not a.stderr
 text=(prior/('control-'+stem+'.wat')).read_text();source=prior/'control.goose'
 pattern=r'i32.const 7(?=\n\s+local.set \d+\n\s+local.get \d+\n\s+i32.wrap_i64\n\s+local.get \d+\n\s+i32.wrap_i64\n\s+local.get \d+\n\s+memory.copy)'
 assert len(re.findall(pattern,text))==1,'loop-copy length not unique'
 short=module('short-'+stem,re.sub(pattern,'i32.const 6',text));failure('short-'+stem,short,source,'assert(s.tail')
 assert len(re.findall(r'i64.const 7(?=\s+i64.mul)',text))==2
 stride=module('stride-'+stem,re.sub(r'i64.const 7(?=\s+i64.mul)','i64.const 8',text,count=1));failure('stride-'+stem,stride,source,'assert(s.mark',b'iteration\n')
 assert len(re.findall(r'i32.const 14(?=\s)',text))==4
 alias=module('alias-'+stem,re.sub(r'i32.const 14(?=\s)','i32.const 0',text));failure('alias-'+stem,alias,source,'assert(s.n')
 owner=(prior/('control-'+stem+'-owner.wat')).read_text();long=module('long-'+stem,re.sub(pattern,'i32.const 8',owner))
 a=run('long-'+stem+'-owner',['node',r/'test/wasm_iteration_owner.mjs',long,'copy'],1);assert b'iteration copy crossed its planned owner image' in a.stderr and not a.stdout
 zero=(prior/('zero_control-'+stem+'-owner.wat')).read_text()
 guard=r'(loop[^\n]*\n)(\s+local.get \d+\n\s+local.get \d+\n\s+i64.load8_u\n\s+i64.ge_u\n\s+br_if [^\n]+\n)(.*?memory.copy\n)'
 assert len(re.findall(guard,zero,re.S))==1
 eager=module('eager-'+stem,re.sub(guard,lambda m:m[1]+m[3]+m[2],zero,count=1,flags=re.S))
 a=run('eager-'+stem+'-owner',['node',r/'test/wasm_iteration_owner.mjs',eager,'zero'],1);assert b'zero-trip iteration copied an element' in a.stderr and not a.stdout
 cleanup=(prior/('checkpoint-'+stem+'-owner.wat')).read_text();start=cleanup.index('(func $main.0');end=cleanup.index('\n  (func ',start)
 main=cleanup[start:end];assert 'global.set 2' in main
 broken=module('cleanup-'+stem,cleanup[:start]+main.replace('global.set 2','drop',1)+cleanup[end:])
 a=run('cleanup-'+stem+'-owner',['node',r/'test/wasm_iteration_owner.mjs',broken,'cleanup'],1);assert b'iteration body data top was not restored at its completion' in a.stderr
 assert a.stdout==b'inner\n','cleanup control failed at the wrong checkpoint'
 # A valid, different data memory must fail the copied-reference assertion.
 modulepath=root/'build01'/('refs_packed-'+stem+'.wasm')
 text=run('packed-'+stem+'-dump',['wasm-tools','print',modulepath]).stdout.decode()
 pattern9=pattern.replace('const 7','const 9');assert len(re.findall(pattern9,text))==1
 at=re.search(pattern9,text).start();copy=text.index('memory.copy',at)
 wrong=module('memory-'+stem,text[:copy]+text[copy:].replace('memory.copy','memory.copy 0 1',1))
 failure('memory-'+stem,wrong,root/'native01/refs_packed.goose','assert(s.value .==')
(p/'summary.json').write_text(json.dumps({'commands':len(rows),'failed':[]},indent=2)+'\n');print('Loop-copy/stride/alias/long-copy/zero-trip/cleanup/memory controls passed.')
