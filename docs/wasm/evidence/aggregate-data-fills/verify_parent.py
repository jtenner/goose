from pathlib import Path
import json,hashlib,subprocess
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend')
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
identity=json.loads((p/'parent-compiler-identity.json').read_text());assert sha(identity['compiler'])==identity['sha256'];parent_source=json.loads(Path('/tmp/goose-wasm-nonfixed-source-20261108/build01/source-hashes.json').read_text());batch=subprocess.Popen(['git','cat-file','--batch'],cwd=r,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
for n,h in parent_source.items():
 batch.stdin.write((identity['parent']+':'+n+'\n').encode());batch.stdin.flush();header=batch.stdout.readline().split();assert header[1]==b'blob';data=batch.stdout.read(int(header[2]));assert batch.stdout.read(1)==b'\n';assert hashlib.sha256(data).hexdigest()==h,n
batch.stdin.close();batch.wait();assert batch.returncode==0
records=json.loads((p/'parent05/results.json').read_text())+json.loads((p/'parent06/results.json').read_text());families={x['case']:x for x in json.loads((p/'positive-families.json').read_text())};assert len(records)==len(families)==43
for x in records:
 f=families[x['case']];assert x['source_sha256']==f['source_sha256']==sha(r/'test/wasm'/(f['fixture']+'.goose'));assert x['expected']==f['expected']==(r/'test/expected'/(f['fixture']+'.out')).read_text()
 phase=p/x['producer_phase']
 for label,index in x['commands'].items():
  prefix=phase/f'command-{index:04}';args=json.loads(prefix.with_suffix('.json').read_text());status=int(prefix.with_suffix('.exit').read_text());err=prefix.with_suffix('.stderr').read_bytes();out=prefix.with_suffix('.stdout').read_bytes()
  if label in ['emit','wasm']:assert args[0]==identity['compiler'] and sha(args[-1])==x['source_sha256']
  if label=='wasm':assert status==1 and b'aggregate data fills need the pending snapshot lowering' in err
  else:assert not status,(x['case'],label,status,err)
  if label=='native':assert out==f['expected'].encode() and not err
for n in ['parent04','parent05','parent06']:assert (p/n/'check.exit').read_text().strip()=='0',n
(p/'parent-verification.json').write_text(json.dumps({'status':'PASS','parent_commit':identity['parent'],'parent_compiler_sha256':identity['sha256'],'committed_tested_source_files':len(parent_source),'native_valid_wasm_compile_failures':43,'families':records,'invalid_setup_attempts':'parent01 field delimiters, parent02 enum delimiter, parent03 overly broad source text replacement; completed native-valid cases reused only after source/status/output checks'},indent=2)+'\n');print('PASS43 native-valid parent compile failures and85 committed parent source hashes')
