from pathlib import Path
import json,hashlib,shutil,gzip
raw=Path(__file__).parent;dest=Path('/home/dev/Projects/goose-wasm-backend/docs/wasm/evidence/array-results');dest.mkdir(exist_ok=True)
records=[]
names={'check.exit','check.stdout','check.stderr','build.exit','build.stdout','build.stderr','checks.py','results.json','cases.json','commands.json','counts.json','source-hashes.json','input-hashes.json','reused.json','report.md'}
for source in sorted(raw.rglob('*')):
 if not source.is_file():continue
 rel=source.relative_to(raw)
 if 'artifacts' in rel.parts:continue
 if source.parent==raw:
  keep=source.suffix in ('.json','.py')
 else:
  keep=(source.name in names or source.suffix=='.goose' or source.name.endswith('-before.stderr')
        or (source.name.startswith('candidate') and source.suffix in ('.stdout','.stderr','.exit'))
        or (rel.parts[0] in ('controls01','controls02','data-image01')
            and source.name.startswith('command-') and source.suffix in ('.stdout','.stderr','.exit')))
 if not keep:continue
 rel=rel
 target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
 records.append({'raw':str(source),'archived':str(rel),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
identity=json.loads((raw/'compiler-identity.json').read_text())
manifest={'status':'PASS','purpose':'correctness only','source_parent':identity['parent'],'compiler_sha256':identity['sha256'],'records':records}
(dest/'archive-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
for row in records:assert hashlib.sha256((dest/row['archived']).read_bytes()).hexdigest()==row['sha256']
print('PASS',len(records),'archived records match raw hashes')
