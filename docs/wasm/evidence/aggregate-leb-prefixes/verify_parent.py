from pathlib import Path
import json,hashlib,subprocess
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend')
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
identity=json.loads((p/'parent-compiler-identity.json').read_text());assert sha(identity['compiler'])==identity['sha256'];source=json.loads(Path('/tmp/goose-wasm-aggregate-data-fill-20261109/build01/source-hashes.json').read_text());batch=subprocess.Popen(['git','cat-file','--batch'],cwd=r,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
for n,h in source.items():
 batch.stdin.write((identity['parent']+':'+n+'\n').encode());batch.stdin.flush();header=batch.stdout.readline().split();assert header[1]==b'blob';data=batch.stdout.read(int(header[2]));assert batch.stdout.read(1)==b'\n';assert hashlib.sha256(data).hexdigest()==h,n
batch.stdin.close();batch.wait();assert not batch.returncode
records=json.loads((p/'parent02/results.json').read_text())+json.loads((p/'parent03/results.json').read_text())+json.loads((p/'parent04/results.json').read_text());families={x['case']:x for x in json.loads((p/'positive-families.json').read_text())};assert len(records)==len(families)==33
for x in records:
 f=families[x['case']];assert x['source_sha256']==f['source_sha256']==sha(r/'test/wasm'/(f['fixture']+'.goose'));assert x['expected']==f['expected']==(r/'test/expected'/(f['fixture']+'.out')).read_text();phase=p/x['producer_phase']
 for label,index in x['commands'].items():
  prefix=phase/f'command-{index:04}';args=json.loads(prefix.with_suffix('.json').read_text());status=int(prefix.with_suffix('.exit').read_text());out=prefix.with_suffix('.stdout').read_bytes();err=prefix.with_suffix('.stderr').read_bytes()
  if label in ['emit','wasm']:assert args[0]==identity['compiler'] and sha(args[-1])==x['source_sha256']
  if label=='wasm':assert status==1 and b'compound array elements need the pending layout lowering' in err
  else:assert not status,(x['case'],label,status,err)
  if label=='native':assert out==f['expected'].encode() and not err
for n in ['parent02','parent03','parent04']:assert (p/n/'check.exit').read_text().strip()=='0',n
(p/'parent-verification.json').write_text(json.dumps({'status':'PASS','parent_commit':identity['parent'],'parent_compiler_sha256':identity['sha256'],'committed_source_files':len(source),'native_valid_wasm_compile_failures':33,'guarded_large_prefix_cases':2,'large_case_limit':'false runtime flag skips large fill body; four- and five-byte reservation paths compile but large payloads are not executed','families':records,'preserved_setup_failures':['parent01 invalid copied-iteration binder spelling;23 valid cases reused','parent05 empty standalone variant element rejected by shared frontend, not backend runtime coverage']},indent=2)+'\n');print('PASS33 native-valid parent compile failures and85 committed parent source hashes')
