from pathlib import Path
import json,hashlib,subprocess
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend')
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
identity=json.loads((p/'parent-compiler-identity.json').read_text());parent=identity['parent']
assert parent=='06ba2c50db69ea6b8ff8b424bfdca2a57b3a8570'
assert sha(identity['compiler'])==identity['sha256']
old=Path(identity['source_stage']);sources=json.loads((old/'build01/source-hashes.json').read_text())
for n,h in sources.items():assert hashlib.sha256(subprocess.check_output(['git','show',parent+':'+n],cwd=r)).hexdigest()==h,n
rows=json.loads((p/'valid-parent-families.json').read_text());assert len(rows)==58 and len({x['case'] for x in rows})==58
for row in rows:
 n=row['case'];q=p/row['phase'];f=q/(n+'.goose');current=r/'test/wasm'/('wasm_aggregate_prefix_'+n+'.goose')
 assert f.read_bytes()==current.read_bytes() and sha(f)==row['source_sha256'],n
 for k in ['emit','cc','native','wasm']:assert int((q/(n+'-'+k+'.exit')).read_text())==row[k+'_exit'],(n,k)
 for k in ['emit','wasm']:
  command=json.loads((q/(n+'-'+k+'.json')).read_text());assert command[0]==identity['compiler'] and command[-1]==str(f),(n,k,command)
 assert all(row[k+'_exit']==0 for k in ['emit','cc','native']) and row['wasm_exit']==1,n
 assert not (q/(n+'-native.stderr')).read_bytes()
 assert (q/(n+'-native.stdout')).read_bytes()==(r/'test/expected'/(current.stem+'.out')).read_bytes(),n
 assert b'compound array elements need the pending layout lowering' in (q/(n+'-wasm.stderr')).read_bytes(),n
 assert not (q/(n+'.wasm')).exists()
slots=json.loads((p/'slot-regression-families.json').read_text());assert len(slots)==18
for row in slots:
 n=row['case'];f=Path(row['source']);current=r/'test/wasm'/(n+'.goose');expected=(r/'test/expected'/(n+'.out')).read_bytes()
 assert f.read_bytes()==current.read_bytes() and sha(f)==row['source_sha256'],n
 for label in (['emit','wasm'] if f.parent.name=='slot-extra01' else ['native-emit','parent-emit']):
  command=json.loads((f.parent/(f.stem+'-'+label+'.json')).read_text());assert command[0]==identity['compiler'] and command[-1]==str(f),(n,label,command)
 assert Path(row['native_exit']).read_text().strip()=='0' and Path(row['native_stdout']).read_bytes()==expected,n
 if row['kind']=='wrong-result':
  assert Path(row['parent_exit']).read_text().strip()=='1' and b'goose runtime error: assert failed at ' in Path(row['parent_stderr']).read_bytes(),n
  assert Path(row['parent_stdout']).read_bytes()!=expected,n
 else:
  assert row['kind']=='supported-copy' and Path(row['parent_exit']).read_text().strip()=='0' and Path(row['parent_stdout']).read_bytes()==expected,n
assert sum(x['kind']=='wrong-result' for x in slots)==17
row=json.loads((p/'dynamic-parent-verification.json').read_text());f=Path(row['source']);current=r/'test/wasm/wasm_aggregate_prefix_owner_dynamic.goose'
assert f.read_bytes()==current.read_bytes() and sha(f)==row['source_sha256']
expected=(r/'test/expected/wasm_aggregate_prefix_owner_dynamic.out').read_bytes()
assert Path(row['native_exit']).read_text().strip()=='0' and Path(row['native_stdout']).read_bytes()==expected
assert Path(row['parent_guest_exit']).read_text().strip()=='0'
assert (p/'dynamic-parent01/node.stdout').read_bytes()==expected
assert Path(row['parent_image_verifier']).read_text().strip()=='0'
assert b'aggregate dynamic data image differs' in (p/'dirty-parent01/command-004.stderr').read_bytes()
prototype=json.loads((p/'build01/compiler-identity.json').read_text());assert sha(p/'build01/goose-tested')==prototype['sha256']
protosource=json.loads((p/'build01/source-hashes.json').read_text())
assert set(protosource)==set(sources)
for n,h in protosource.items():
 if h!=sources[n]:assert sha(p/'build01'/(Path(n).name+'.txt'))==h,n
record={'status':'PASS','source_commit':parent,'compiler_sha256':identity['sha256'],'source_hashes_match_commit':len(sources),'native_valid_compile_failures':58,'native_valid_stale_slot_failures':17,'stored_copy_regressions':1,'dynamic_parent_active_values_pass_and_dirty_image_fails':True,'retained_initial_prototype_sha256':prototype['sha256'],'families':rows,'slot_families':slots}
(p/'parent-verification.json').write_text(json.dumps(record,indent=2)+'\n');print('PASS 58 compilation failures,17 wrong results,stored-copy regression and dirty-image failure; compiler/source identities')
