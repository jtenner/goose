from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');expected=(r/'test/expected/wasm_inline_ref_abi_packed.out').read_bytes();rows=[];healthy=p.parent/'build04/candidate/wasm_inline_ref_abi_packed-O0.wasm';image=None
for name,module in [('healthy',healthy),('print-owner',p/'controls/print-owner.wasm'),('snapshot-owner',p/'controls/snapshot-owner.wasm')]:
 out=p/(name+'-instance');command=['node',str(p/'before/test/wasm_reference_abi.mjs'),str(module),str(out)];a=subprocess.run(command,cwd=r,capture_output=True,timeout=90)
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:(p/(name+'.'+ext)).write_bytes(data)
 row={'name':name,'command':command,'actual_exit':a.returncode,'expected_exit':0 if name=='healthy' else 1,'guest_output_matches':a.stdout==expected}
 assert a.stdout==expected,(name,'control did not preserve expected output',a.stderr)
 if out.exists():
  state=json.loads((out/'instance.json').read_text());row['recorded_instance']=state
  if image is None:image=state
  row['memory_matches_healthy']=state['memories']==image['memories'];assert row['memory_matches_healthy']
 rows.append(row);(p/'before-results.json').write_text(json.dumps(rows,indent=2)+'\n')
assert rows[0]['actual_exit']==0
accepted=[x['name'] for x in rows[1:] if x['actual_exit']==0]
assert not accepted,'Original owner assertion accepted damaged controls: '+','.join(accepted)
