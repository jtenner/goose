from pathlib import Path
import json,hashlib,gzip,shutil
raw=Path(__file__).parent;dest=Path('/home/dev/Projects/goose-wasm-backend/docs/wasm/evidence/limited-array-conversion');dest.mkdir(exist_ok=True)
records=[]
for source in sorted(raw.rglob('*')):
 if not source.is_file():continue
 rel=source.relative_to(raw)
 if 'artifacts' in rel.parts:continue
 keep=source.suffix in ('.json','.py','.mjs','.goose','.md','.stdout','.stderr','.exit','.txt','.wat')
 # Preserve exact failing generated C and one repaired example, without
 # copying every repeated runtime prelude into the source archive.
 if source.suffix=='.c':keep=False
 if not keep:continue
 data=source.read_bytes();compress=source.suffix in ('.c','.wat') or (len(data)>65536) or data.endswith(b'\n\n') or any(x.rstrip(b'\r\n').endswith((b' ',b'\t')) for x in data.splitlines(keepends=True))
 archived=str(rel)+('.gz' if compress else '');target=dest/archived;target.parent.mkdir(parents=True,exist_ok=True)
 target.write_bytes(gzip.compress(data,mtime=0) if compress else data)
 row={'raw':str(source),'archived':archived,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
 if compress:
  row.update(raw_sha256=hashlib.sha256(data).hexdigest(),encoding='gzip');assert gzip.decompress(target.read_bytes())==data
  previous=dest/rel
  if previous.exists():
   assert previous.read_bytes()==data
   previous.unlink()
 records.append(row)
identity=json.loads((raw/'compiler-identity.json').read_text())
(dest/'archive-manifest.json').write_text(json.dumps({'status':'PASS','purpose':'correctness only','source_parent':identity['parent'],'compiler_sha256':identity['sha256'],'records':records},indent=2)+'\n')
print('PASS',len(records),'archived records')
