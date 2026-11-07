from pathlib import Path
import subprocess,json,hashlib,sys
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');exe=p.parent/'build04/goose-tested';commands=[];rows=[]
sys.path.insert(0,str(r/'test'));from wasm_backend import function_local_counts

def run(name,args):
 a=subprocess.run([str(x) for x in args],cwd=r,capture_output=True,timeout=120)
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:(p/(name+'.'+ext)).write_bytes(data)
 commands.append({'name':name,'args':[str(x) for x in args],'exit':a.returncode});(p/'commands-results.json').write_text(json.dumps(commands,indent=2)+'\n');assert a.returncode==0,(name,a.stderr.decode(errors='replace'));return a
for kind in ['limited-literal','fill-and-text']:
 for amount in [32,256]:
  if kind=='limited-literal':
   fields='mark: u8, cells: u16[..3], tail: u8';value='Row { mark: 1, cells: [7, 8], tail: 2 }';check='assert(row.mark == 1); assert(row.cells.len == 2); assert(row.cells[0] == 7); assert(row.cells[1] == 8); assert(row.tail == 2);'
  else:
   fields='mark: u8, cells: u16[2], text: u8[3], zero: u32[2] = default<u32[2]>(), tail: u8';value='Row { mark: 1, cells: [7; 2], text: "abc", tail: 2 }';check='assert(row.mark == 1); assert(row.cells[0] == 7); assert(row.cells[1] == 7); assert(row.text[0] == 97); assert(row.text[2] == 99); assert(row.zero[0] == 0); assert(row.zero[1] == 0); assert(row.tail == 2);'
  source=p/f'{kind}-{amount}.goose';source.write_text('struct Row { '+fields+' }\nfn main() { var rows: Row[] = ['+', '.join([value]*amount)+']; assert(rows.len == '+str(amount)+'); for &row in rows { '+check+' } print("scaling=ok"); }\n')
  for opt in [0,2]:
   name=f'{kind}-{amount}-O{opt}';c=p/(name+'.c');native=p/(name+'.native');module=p/(name+'.wasm');expected=b'scaling=ok\n'
   run(name+'-native-emit',[exe,'-O'+str(opt),'--standalone','-o',c,source]);run(name+'-native-build',['cc','-O0',c,'-pthread','-lm','-ldl','-o',native]);a=run(name+'-native-run',[native]);assert a.stdout==expected and not a.stderr
   run(name+'-emit',[exe,'-O'+str(opt),'--target','wasm','-o',module,source]);run(name+'-validate',['wasm-tools','validate',module]);a=run(name+'-node',['node',r/'test/wasm_reference_abi.mjs',module,p/(name+'-instance')]);assert a.stdout==expected and not a.stderr
   a=run(name+'-wasmtime',['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',module]);assert a.stdout==expected and not a.stderr
   image=(p/(name+'-instance')/'data_memory_1.bin').read_bytes();state=json.loads((p/(name+'-instance')/'instance.json').read_text());assert state['completionCalls']==1 and state['pendingPrints']==state['pendingSnapshots']==0
   payload=(bytes([1,2,7,0,8,0,0,0,2]) if kind=='limited-literal' else bytes([1,7,0,7,0,97,98,99])+bytes(8)+bytes([2]))*amount
   model=bytes(1)+amount.to_bytes(4,'little')+payload;assert image==model+bytes(len(image)-len(model)),(name,'full data memory differs from independent packed-byte model')
   counts=function_local_counts(module.read_bytes());rows.append({'kind':kind,'amount':amount,'opt':opt,'local_counts':counts,'module_bytes':module.stat().st_size,'module_sha256':hashlib.sha256(module.read_bytes()).hexdigest(),'native_and_both_engine_checks':'PASS','full_data_memory_model':'PASS'});(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
failures=[]
for kind in ['limited-literal','fill-and-text']:
 for opt in [0,2]:
  pair=[x for x in rows if x['kind']==kind and x['opt']==opt]
  if pair[0]['local_counts']!=pair[1]['local_counts']:failures.append({'kind':kind,'opt':opt,'counts32':pair[0]['local_counts'],'counts256':pair[1]['local_counts']})
(p/'footprint-assertion.json').write_text(json.dumps({'constant_constructor_scratch':not failures,'failures':failures},indent=2)+'\n')
assert not failures,failures
print('8scaling cases and full data-memory models pass; constructor locals constant from32to256rows.')
