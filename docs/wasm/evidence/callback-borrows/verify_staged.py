from pathlib import Path
import json,hashlib,gzip,subprocess
raw=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');planned=json.loads((raw/'planned-paths.json').read_text());sha=lambda b:hashlib.sha256(b).hexdigest()
a=subprocess.run(['git','diff','--cached','--check'],cwd=r,capture_output=True);assert not a.returncode,(a.stdout,a.stderr)
names=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).decode().strip('\0').split('\0');assert set(names)==set(planned),(set(names)-set(planned),set(planned)-set(names))
a=subprocess.run(['git','cat-file','--batch'],cwd=r,input=''.join(':'+n+'\n' for n in names).encode(),capture_output=True);assert not a.returncode,a.stderr;data=a.stdout;cursor=0
for n in names:
 end=data.index(b'\n',cursor);header=data[cursor:end].split();assert header[1]==b'blob',header;length=int(header[2]);cursor=end+1;blob=data[cursor:cursor+length];cursor+=length;assert data[cursor:cursor+1]==b'\n';cursor+=1;assert sha(blob)==planned[n]==sha((r/n).read_bytes()),n
assert cursor==len(data)
manifest=json.loads((r/'docs/wasm/evidence/callback-borrows/archive-manifest.json').read_text())
for row in manifest['records']:
 b=(r/'docs/wasm/evidence/callback-borrows'/row['archived']).read_bytes();assert sha(b)==row['sha256'];b=gzip.decompress(b) if row.get('encoding')=='gzip' else b;assert b==Path(row['raw']).read_bytes(),row['raw']
assert json.loads((raw/'final-validation.json').read_text())['status']=='PASS'
(raw/'staged-verification.json').write_text(json.dumps({'status':'PASS','staged_paths':len(planned),'archived_records':len(manifest['records']),'all_staged_blobs_and_raw_hashes':True},indent=2)+'\n');print('PASS',len(planned),'staged blobs and',len(manifest['records']),'raw evidence records')
