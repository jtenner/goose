from pathlib import Path
import subprocess,json,hashlib,gzip
p=Path(__file__).parent;r=Path.cwd()
def staged(n):return subprocess.check_output(['git','show',':'+n])
m=json.loads((p/'staged-source-test-hashes.json').read_text())
for n,sha in m.items():assert hashlib.sha256(staged(n)).hexdigest()==sha,n
base='docs/wasm/evidence/fixed-array-assignment-layout/'
manifest=json.loads(staged(base+'archive-manifest.json'))
for row in manifest['records']:
 b=staged(base+row['archived']);assert hashlib.sha256(b).hexdigest()==row['sha256'],row
 raw=Path(row['raw']).read_bytes()
 assert (gzip.decompress(b) if row.get('encoding')=='gzip' else b)==raw,row
f=json.loads(staged(base+'final-validation.json'));assert f['status']=='PASS' and f['wasm_checks']==4999
assert not subprocess.run(['git','diff','--quiet']).returncode,'unstaged change'
assert not subprocess.check_output(['git','ls-files','--others','--exclude-standard']).strip(),'untracked change'
assert not subprocess.run(['git','diff','--cached','--check']).returncode
record={'status':'PASS','staged_source_tests':len(m),'archive_records':len(manifest['records']),'final_validation_status':f['status'],'compiler_sha256':f['compiler_sha256'],'no_unstaged_changes':True}
(p/'staged-verification.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
