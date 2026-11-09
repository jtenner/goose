from pathlib import Path
import subprocess,json,hashlib,gzip
p=Path(__file__).parent;r=Path.cwd();index={}
for row in subprocess.check_output(['git','ls-files','-s','-z']).split(b'\0'):
 if not row:continue
 meta,name=row.split(b'\t',1);mode,oid,stage=meta.split();assert stage==b'0'
 index[name.decode()]=oid
batch=subprocess.Popen(['git','cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
def staged(n):
 assert n in index,n
 batch.stdin.write(index[n]+b'\n');batch.stdin.flush()
 header=batch.stdout.readline().split();assert len(header)==3 and header[0]==index[n] and header[1]==b'blob',(n,header)
 size=int(header[2]);data=batch.stdout.read(size);assert len(data)==size and batch.stdout.read(1)==b'\n',n
 return data
try:
 m=json.loads((p/'staged-source-test-hashes.json').read_text())
 for n,sha in m.items():assert hashlib.sha256(staged(n)).hexdigest()==sha,n
 base='docs/wasm/evidence/aggregate-leb-prefixes/'
 manifest=json.loads(staged(base+'archive-manifest.json'))
 for row in manifest['records']:
  b=staged(base+row['archived']);assert hashlib.sha256(b).hexdigest()==row['sha256'],row
  raw=Path(row['raw']).read_bytes()
  assert (gzip.decompress(b) if row.get('encoding')=='gzip' else b)==raw,row
 f=json.loads(staged(base+'final-validation.json'));assert f['status']=='PASS' and f['wasm_checks']==7991
 assert not subprocess.run(['git','diff','--quiet']).returncode,'unstaged change'
 assert not subprocess.check_output(['git','ls-files','--others','--exclude-standard']).strip(),'untracked change'
 assert not subprocess.run(['git','diff','--cached','--check']).returncode
 record={'status':'PASS','staged_source_tests':len(m),'archive_records':len(manifest['records']),'final_validation_status':f['status'],'compiler_sha256':f['compiler_sha256'],'no_unstaged_changes':True,'git_blob_reader':'one cat-file batch process'}
finally:
 batch.stdin.close();batch.wait();assert batch.returncode==0,batch.stderr.read()
(p/'staged-verification.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
