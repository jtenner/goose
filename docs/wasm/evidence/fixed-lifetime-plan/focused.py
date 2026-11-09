from pathlib import Path
import subprocess,json,hashlib
raw=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');p=raw/'focused01';p.mkdir(exist_ok=True);identity=json.loads((raw/'compiler-identity.json').read_text());exe=Path(identity['compiler']);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(exe)==identity['sha256'];rows=[];serial=0
modules={(x['source'],x['opt']):x['sha256'] for x in json.loads((raw/'identity02/results.json').read_text())}
def run(args):
 global serial
 serial+=1;args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120);prefix=p/f'command-{serial:04}'
 prefix.with_suffix('.json').write_text(json.dumps(args)+'\n');prefix.with_suffix('.stdout').write_bytes(a.stdout);prefix.with_suffix('.stderr').write_bytes(a.stderr);prefix.with_suffix('.exit').write_text(str(a.returncode)+'\n');assert not a.returncode,(args,a.stderr);return a
names=['constructor_assignment_targets', 'constructor_assignment_nested_assignment', 'constructor_assignment_aggregate_exit', 'constructor_assignment_abandon', 'constructor_assignment_growth', 'compound_math_scalar_effect', 'compound_math_snapshot_owner', 'compound_math_rebind', 'array_argument_callback_exit', 'array_argument_later_return', 'array_argument_limited', 'array_argument_dynamic_source', 'array_expression_source_fixed_block', 'array_expression_source_limited_void_branch', 'fixed_array_conversion_scalar_order', 'fixed_result_argument']
for n in names:
 f=r/'test/wasm'/('wasm_'+n+'.goose');expected=(r/'test/expected'/(f.stem+'.out')).read_bytes()
 for opt in (0,2):
  prefix=p/(f.stem+f'-O{opt}');c,native,wasm=[prefix.with_suffix(e) for e in ['.c','.native','.wasm']]
  run([exe,f'-O{opt}','--standalone','-o',c,f]);run(['cc',f'-O{opt}',c,'-pthread','-lm','-ldl','-o',native]);a=run([native]);assert a.stdout==expected and not a.stderr
  run([exe,f'-O{opt}','--target','wasm','-o',wasm,f]);assert sha(wasm)==modules[str(f.relative_to(r)),opt]
  run(['wasm-tools','validate',wasm])
  for host,args in [('node',['node',r/'test/wasm_reference_abi.mjs',wasm,p/(f.stem+f'-O{opt}-instance')]),('wasmtime',['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',wasm])]:
   a=run(args);assert a.stdout==expected and not a.stderr,(f.name,opt,host,a.stdout,a.stderr)
  rows.append({'source':str(f.relative_to(r)),'source_sha256':sha(f),'opt':opt,'module_sha256':sha(wasm),'status':'PASS native/Node/Wasmtime'});(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print('PASS',len(rows),'fresh native/Node/Wasmtime assignment and temporary pairs')
