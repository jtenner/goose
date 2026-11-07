from pathlib import Path
import json,hashlib,subprocess
P=Path('/tmp/goose-wasm-data-aggregates-review-20261107');R=Path('/tmp/goose-wasm-data-aggregates-20261107');W=Path('/home/dev/Projects/goose-wasm-backend');A=P/'snapshot/docs/wasm/evidence/data-aggregates';O=P/'review';rec={'archive':[],'manifests':{},'errors':[]}
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def j(p):return json.loads(Path(p).read_text())
for row in j(A/'archive-manifest.json'):
 d=dict(row);d['raw_actual']=h(row['source']);d['archive_actual']=h(A/row['archived']);d['match']=d['raw_actual']==d['archive_actual']==row['sha256'];rec['archive'].append(d)
 if not d['match']:rec['errors'].append(d)
for unit,root in [('build05',W),('build04',R/'e1-source-reconstruction')]:
 fs=j(R/unit/'source-hashes.json'); bad=[n for n,v in fs.items() if h(root/n)!=v];rec['manifests'][unit]={'count':len(fs),'mismatches':bad};rec['errors']+=bad
b4=j(R/'build04/source-hashes.json');b5=j(R/'build05/source-hashes.json');rec['changed_cpp_build04_to_build05']=[n for n,v in b4.items() if b5[n]!=v]
parent=Path('/tmp/goose-wasm-inline-ref-abi-20261107/build04');bad=[]
for n,v in j(parent/'source-hashes.json').items():
 x=subprocess.run(['git','--no-optional-locks','-C',str(W),'show','4dc9af871426b6f440f5bdbe7f009531f4d72600:'+n],capture_output=True)
 if x.returncode or hashlib.sha256(x.stdout).hexdigest()!=v:bad.append(n)
rec['parent_source_mismatches']=bad;rec['errors']+=bad
parser=j(R/'build05/static-parser-provenance.json');x=subprocess.run(['git','--no-optional-locks','-C',str(W),'show','4dc9af871426b6f440f5bdbe7f009531f4d72600:'+parser['path']],capture_output=True);rec['static_parser']={'claimed':parser['sha256'],'baseline':h(P/'baseline'/parser['path']),'git':hashlib.sha256(x.stdout).hexdigest(),'current':h(W/parser['path'])}
for unit in ['scaling-before01','unknown-scaling-before01']:
 d=j(R/unit/'inputs.json');rec['static_parser'][unit]=str(d.get(parser['path'], 'not in map')) if isinstance(d,dict) else 'list'
for u in ['full-wasm04','compatibility02']:
 d=j(R/u/'validation-input-hashes.json');bad=[n for n,v in d.items() if h(W/n)!=v];rec['manifests'][u]={'count':len(d),'mismatches':bad}
# Logs and exit values are content checks, distinct from hashes.
exits={};stderr={}
for f in A.rglob('*.exit'):
 exits[str(f.relative_to(A))]=f.read_text().strip()
for f in A.rglob('*.stderr'):
 if f.stat().st_size:stderr[str(f.relative_to(A))]=f.read_text(errors='replace')
rec['exit_values']=exits;rec['nonempty_stderr']=stderr
(O/'archive-and-provenance.json').write_text(json.dumps(rec,indent=2)+'\n')
print('ARCHIVE',len(rec['archive']),'ERRORS',rec['errors']);print('MANIFESTS',rec['manifests']);print('CPP CHANGES',rec['changed_cpp_build04_to_build05']);print('PARSER',rec['static_parser']);print('EXITS',len(exits),'NONZERO', {n:v for n,v in exits.items() if v!='0'});print('STDERR paths',[(n,len(v)) for n,v in stderr.items()])
