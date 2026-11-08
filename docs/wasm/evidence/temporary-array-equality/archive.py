from pathlib import Path
import json,hashlib,shutil,gzip
raw=Path(__file__).parent;dest=Path('/home/dev/Projects/goose-wasm-backend/docs/wasm/evidence/temporary-array-equality');dest.mkdir(exist_ok=True)
previous=json.loads((dest/'archive-manifest.json').read_text())['records'] if (dest/'archive-manifest.json').exists() else []
records=[]
names={'check.exit','check.stdout','check.stderr','build.exit','build.stdout','build.stderr','checks.py','results.json','cases.json','commands.json','counts.json','source-hashes.json','input-hashes.json','reused.json','report.md','check02.exit','check02.stdout','check02.stderr','checks02.py','commands02.json','scope-correction.json'}
for source in sorted(raw.rglob('*')):
 if not source.is_file():continue
 rel=source.relative_to(raw)
 if 'artifacts' in rel.parts:continue
 if source.parent==raw:
  keep=source.suffix in ('.json','.py') or source.name=='plan.md'
 else:
  keep=(source.name in names or source.suffix=='.goose' or source.name.endswith('-before.stderr')
        or (source.name.startswith('candidate') and source.suffix in ('.stdout','.stderr','.exit'))
        or (rel.parts[0] in ('focused01','focused02','warning02')
            and source.name.startswith('command-') and source.suffix in ('.stdout','.stderr','.exit')))
 if source.name.endswith('.patch') or (keep and any(line.rstrip(b'\r\n').endswith((b' ', b'\t')) for line in source.read_bytes().splitlines(keepends=True))):
  target=dest/(str(rel)+'.gz');target.parent.mkdir(parents=True,exist_ok=True)
  target.write_bytes(gzip.compress(source.read_bytes(),mtime=0))
  assert gzip.decompress(target.read_bytes())==source.read_bytes()
  original=dest/rel
  if original.exists():
   assert original.read_bytes()==source.read_bytes()
   original.unlink()
  records.append({'raw':str(source),'archived':str(rel)+'.gz','sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'raw_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'encoding':'gzip'})
  continue
 if not keep:continue
 rel=rel
 target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
 records.append({'raw':str(source),'archived':str(rel),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
identity=json.loads((raw/'compiler-identity.json').read_text())
manifest={'status':'PASS','purpose':'correctness only','source_parent':identity['parent'],'compiler_sha256':identity['sha256'],'records':records}
retained={row['archived'] for row in records}
for row in previous:
 if row['archived'] in retained:continue
 old=dest/row['archived'];original=Path(row['raw'])
 assert original.exists() and hashlib.sha256(old.read_bytes()).hexdigest()==row['sha256']
 payload=gzip.decompress(old.read_bytes()) if row.get('encoding')=='gzip' else old.read_bytes()
 assert payload==original.read_bytes()
 old.unlink()
(dest/'archive-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
for row in records:assert hashlib.sha256((dest/row['archived']).read_bytes()).hexdigest()==row['sha256']
print('PASS',len(records),'archived records match raw hashes')
