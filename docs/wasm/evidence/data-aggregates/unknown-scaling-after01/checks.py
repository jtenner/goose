from pathlib import Path
import subprocess,json,hashlib,sys
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');exe=p.parent/'build05/goose-tested';commands=[];rows=[]
sys.path.insert(0,str(r/'test'));from wasm_backend import function_local_counts

def run(name,args):
 a=subprocess.run([str(x) for x in args],cwd=r,capture_output=True,timeout=120)
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:(p/(name+'.'+ext)).write_bytes(data)
 commands.append({'name':name,'args':[str(x) for x in args],'exit':a.returncode});(p/'commands-results.json').write_text(json.dumps(commands,indent=2)+'\n');assert a.returncode==0,(name,a.stderr.decode(errors='replace'));return a
def verify_native(name,source,expected):
 reuse=json.loads((p/'verified-native-reuse.json').read_text());old=Path(reuse['source'])
 for file,sha in reuse['files'].items():assert hashlib.sha256((old/file).read_bytes()).hexdigest()==sha,file
 assert source.parent==old
 assert (old/(name+'-native-run.exit')).read_text().strip()=='0'
 assert (old/(name+'-native-run.stdout')).read_bytes()==expected and not (old/(name+'-native-run.stderr')).read_bytes()

for amount in [32,256]:
 source=p.parent/'unknown-scaling-before01'/f'unknown-{amount}.goose';value='Row { mark: 1, cells: [7, 8], tail: 2 }'
 expected_source=('struct Row { mark: u8, cells: u16[..3], tail: u8 }\nrecursive fn make() -> i64 { var rows: Row[] = ['+', '.join([value]*amount)+']; assert(rows.len == '+str(amount)+'); var i: i64 = 0; while i < rows.len { assert(rows[i].mark == 1); assert(rows[i].cells.len == 2); assert(rows[i].cells[0] == 7); assert(rows[i].cells[1] == 8); assert(rows[i].tail == 2); i++; } return rows[rows.len - 1].cells[1]; }\nfn main() { assert(make() == 8); var keep: i64[] = [91]; assert(make() == 8); assert(keep[0] == 91); print("unknown=ok"); }\n')
 assert source.read_text()==expected_source
 name=f'unknown-{amount}';c=p/(name+'.c');native=p/(name+'.native');module=p/(name+'.wasm');expected=b'unknown=ok\n'
 verify_native(name,source,expected)
 run(name+'-emit',[exe,'-O0','--target','wasm','-o',module,source]);run(name+'-validate',['wasm-tools','validate',module]);a=run(name+'-node',['node',r/'test/wasm_reference_abi.mjs',module,p/(name+'-instance')]);assert a.stdout==expected and not a.stderr
 a=run(name+'-wasmtime',['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',module]);assert a.stdout==expected and not a.stderr
 run(name+'-wat',['wasm-tools','print',module])
 old_images=p.parent/'unknown-scaling-before01'/(name+'-instance')
 for image_file in old_images.glob('*.bin'):assert image_file.read_bytes()==(p/(name+'-instance')/image_file.name).read_bytes(),(name,image_file.name)
 blob=bytes(1)+amount.to_bytes(4,'little')+bytes([1,2,7,0,8,0,0,0,2])*amount
 for memory in [1,2]:
  image=(p/(name+'-instance')/f'data_memory_{memory}.bin').read_bytes();model=bytearray(blob+bytes(len(image)-len(blob)))
  if memory==1:model[1:5]=(1).to_bytes(4,'little');model[5:13]=(91).to_bytes(8,'little')
  assert image==model,(name,memory,'full memory model differs')
 counts=function_local_counts(module.read_bytes());rows.append({'amount':amount,'local_counts':counts,'function_count':len(counts),'module_bytes':module.stat().st_size,'module_sha256':hashlib.sha256(module.read_bytes()).hexdigest(),'semantics_and_full_memory_model':'PASS'});(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
result={'constant_function_count':rows[0]['function_count']==rows[1]['function_count'],'counts':[x['function_count'] for x in rows],'constant_local_counts':rows[0]['local_counts']==rows[1]['local_counts']};(p/'footprint-assertion.json').write_text(json.dumps(result,indent=2)+'\n');assert result['constant_function_count'] and result['constant_local_counts'],result
