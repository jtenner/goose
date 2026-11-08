from pathlib import Path
import subprocess,sys,json,hashlib,re
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;sys.path.insert(0,str(r/'test'))
from wasm_fixed_binary_checks import emit
from wasm_data_iteration_checks import function_span
i=0
def run(args,ok=True):
 global i
 i+=1;args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120)
 (p/f'command-{i:03}.json').write_text(json.dumps(args)+'\n')
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/f'command-{i:03}.{k}').write_bytes(v)
 assert not ok or a.returncode==0,(args,a.returncode,a.stderr)
 return a
source=p/'u64-sum.goose';source.write_text('fn main(){var a:i64[u32]=[7,-8,900];print("before");var b:i64[u64]=copy(a);print("after");assert(b.len==3&&b[0]==7&&b[1]== -8&&b[2]==900&&a.len==3);}\n')
owner=(r/'test/wasm_array_prefix_conversion_owner.mjs').read_text().replace("'../scripts/",f"'{r}/scripts/").replace("'./wasm_",f"'{r}/test/wasm_")
owner=owner.replace('overflow:[8,4,3,8]','overflow:[4,8,3,8]').replace('else assert.equal(source.readUInt16LE(1),count);','else if(sourcePrefix===4)assert.equal(source.readUInt32LE(1),count);else assert.equal(source.readUInt16LE(1),count);').replace("else if(targetPrefix===4)target.writeUInt32LE(count,1);", "else if(targetPrefix===8)target.writeBigUInt64LE(BigInt(count),1);else if(targetPrefix===4)target.writeUInt32LE(count,1);")
(p/'owner.mjs').write_text(owner)
failure=(r/'test/wasm_array_prefix_conversion_failure.mjs').read_text().replace("'../scripts/",f"'{r}/scripts/").replace("'./wasm_",f"'{r}/test/wasm_")
failure=failure.replace("const width=overflow?8:count===256?2:4", "const width=overflow?4:count===256?2:4").replace('source.writeBigUInt64LE(536870912n,1)','source.writeUInt32LE(536870911,1)');(p/'failure.mjs').write_text(failure)
(p/'helper-input-hashes.json').write_text(json.dumps({n:hashlib.sha256((r/n).read_bytes()).hexdigest() for n in ['test/wasm_array_prefix_conversion_owner.mjs','test/wasm_array_prefix_conversion_failure.mjs']},indent=2)+'\n')
exe=p.parent/'build01/goose-tested';parent=Path('/tmp/goose-wasm-array-expression-source-20261108/build01/goose-tested');rows=[]
for opt in [0,2]:
 stem=p/f'u64-sum-O{opt}';c,native,module=(stem.with_suffix(ext) for ext in ['.c','.native','.wasm'])
 run([parent,f'-O{opt}','--standalone','-o',c,source]);run(['cc',c,'-pthread','-lm','-ldl','-o',native]);assert run([native]).stdout==b'before\nafter\n'
 result=run([parent,f'-O{opt}','--target','wasm','-o',module,source],ok=False);assert result.returncode==1 and b'array adaptation needs the pending destination lowering' in result.stderr and not module.exists()
 run([exe,f'-O{opt}','--target','wasm','-o',module,source]);run(['wasm-tools','validate',module]);assert run(['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',module]).stdout==b'before\nafter\n'
 text=run(['wasm-tools','print',module]).stdout.decode();derived=emit(run,'wasm-tools',p,stem.name+'-healthy',text,3)
 assert run(['node',p/'owner.mjs',derived,'overflow']).stdout==b'before\nafter\n'
 assert run(['node',p/'failure.mjs',derived,'overflow']).stdout==b'before\n'
 a,z=function_span(text,'main');body=text[a:z]
 pattern=r'i64.extend_i32_u\n\s*local.get \d+\n\s*i64.extend_i32_u\n\s*i64.add\n\s*local.tee \d+\n\s*i64.const 4294967295\n\s*i64.gt_u'
 changed,n=re.subn(pattern,lambda m:m[0].replace('i64.gt_u','i64.lt_u'),body);assert n==1,n
 bad=emit(run,'wasm-tools',p,stem.name+'-guard',text[:a]+changed+text[z:],3);result=run(['node',p/'failure.mjs',bad,'overflow'],ok=False)
 assert result.returncode==1 and b'RuntimeError: memory access out of bounds' in result.stderr,result.stderr
 rows.append({'opt':opt,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'module_sha256':hashlib.sha256(module.read_bytes()).hexdigest(),'status':'PASS native-valid parent failure / u64 full-image healthy / damaged sum guard'})
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS two u64 receiver native/Node/Wasmtime pairs and two damaged-count/sum-guard controls')
