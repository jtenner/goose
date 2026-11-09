from pathlib import Path
import hashlib,json,subprocess
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend')
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
identity=json.loads((p/'parent-compiler-identity.json').read_text());assert sha(identity['compiler'])==identity['sha256'];parent_source=json.loads(Path(identity['source_hashes']).read_text());assert len(parent_source)==85
batch=subprocess.Popen(['git','cat-file','--batch'],cwd=r,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
for n,h in parent_source.items():
 batch.stdin.write((identity['parent']+':'+n+'\n').encode());batch.stdin.flush();header=batch.stdout.readline().split();assert len(header)==3 and header[1]==b'blob';data=batch.stdout.read(int(header[2]));assert batch.stdout.read(1)==b'\n';assert hashlib.sha256(data).hexdigest()==h,n
batch.stdin.close();batch.wait();assert batch.returncode==0
families=json.loads((p/'positive-families.json').read_text());rows=[]
for x in families:
 fixture=r/'test/wasm'/(x['fixture']+'.goose');expected=(r/'test/expected'/(x['fixture']+'.out')).read_bytes();assert sha(fixture)==x['source_sha256'] and expected==x['expected'].encode()
 phase=p/x['producer_phase'];assert (phase/'check.exit').read_text().strip()=='0' or x['producer_phase']=='parent02'
 for label,index in x['commands'].items():
  prefix=phase/f'command-{index:04}';args=json.loads(prefix.with_suffix('.json').read_text());status=int(prefix.with_suffix('.exit').read_text());err=prefix.with_suffix('.stderr').read_bytes();stdout=prefix.with_suffix('.stdout').read_bytes()
  if label in ['emit','wasm']:assert args[0]==identity['compiler'] and sha(args[-1])==x['source_sha256']
  if label=='wasm' and x['kind']=='missing-conversion':assert status==1 and b'array adaptation needs the pending destination lowering' in err
  else:assert status==0,(x['case'],label,status,err)
  if label=='native':assert stdout==expected and not err
 rows.append({'source':str(fixture.relative_to(r)),'kind':x['kind'],'producer':x['producer_phase'],'source_sha256':x['source_sha256']})
assert len(rows)==69 and sum(x['kind']=='missing-conversion' for x in rows)==67 and sum(x['kind']=='parent-supported' for x in rows)==2
for n in ['parent03','parent04','parent05','parent06','parent07','parent08','parent09','failure-parent01']:assert (p/n/'check.exit').read_text().strip()=='0',n
failure=json.loads((p/'failure-parent01/results.json').read_text());assert len(failure)==4 and all(x['status']=='PASS native specific runtime range failure; parent Wasm missing conversion' for x in failure)
record={'status':'PASS','parent_commit':identity['parent'],'parent_compiler_sha256':identity['sha256'],'committed_parent_source_files':len(parent_source),'positive_families':len(rows),'native_valid_compile_failures':67,'parent_supported_regressions':2,'native_valid_range_failure_pairs':4,'families':rows,'retained_compound_guard':'parent03 native-valid grow_indexed_reference and current images01 two optimization checks','invalid_original_recursion_sketch':'shared frontend rejected recursive call while nonfixed owner live; corrected scoped source used for positive family','preserved_failures':['parent02 invalid recursive sketch','focused01 harness insertion setup','images03 sum guard helper selected later index comparison']}
(p/'parent-verification.json').write_text(json.dumps(record,indent=2)+'\n');print('PASS 67 native-valid compile failures, 2 supported regressions, 4 range failures; all85 committed parent source hashes')
