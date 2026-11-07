from pathlib import Path
import hashlib,json,shutil
r=Path('/home/dev/Projects/goose-wasm-backend');raw=Path(__file__).parent;dest=r/'docs/wasm/evidence/fixed-aggregate-arrays'
dest.mkdir(exist_ok=True)
units=['native01','build01','build02','paths01','paths02','full-wasm01','native-baseline01','compatibility01']
manifest={}
for unit in units:
 p=raw/unit
 for f in sorted(p.rglob('*')):
  if not f.is_file() or '__pycache__' in f.parts:continue
  rel=f.relative_to(raw);data=f.read_bytes();manifest[str(rel)]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
  # Keep commands, source fixtures, raw statuses/stderr and compact summaries.
  # The complete artifact inventory also identifies generated C and executables.
  keep=f.parent==p and f.suffix in ('.json','.py','.goose','.stdout','.stderr','.exit')
  if unit=='compatibility01' and f.relative_to(p).parts[0]=='exact' and f.name=='summary.json':keep=True
  if keep:
   to=dest/rel;to.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,to)
for name in ['resource-unit.py','scope.md','promoted.json','promotion-extension.json','gate-cases.json','additional-gates.json','archive.py']:
 shutil.copyfile(raw/name,dest/name)
(dest/'artifact-hashes.json').write_text(json.dumps(manifest,indent=2)+'\n')
# The full suite stores generated artifacts, not a separate command log.
modules={str(f.relative_to(raw/'full-wasm01/artifacts')):{'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size} for f in sorted((raw/'full-wasm01/artifacts').glob('*.wasm'))}
(dest/'final-modules.json').write_text(json.dumps(modules,indent=2)+'\n')
(dest/'reconstruction.json').write_text(json.dumps({'baseline':'0d64e43d32f17485526beef0d463e9c9abad9102','compiler_sha256':'bd3856b6c2eedd69bd4eaf343aa9f505794f1a17ab3383194b218fbe33fa368d','raw_root':str(raw),'archive':'Compact commands, scripts, fixture sources, stdout/stderr/status and manifests. Full generated C, native binaries and modules stay in raw_root.','timing_samples':0},indent=2)+'\n')
print('Archived',len(manifest),'artifact identities and',len(modules),'final modules.')
