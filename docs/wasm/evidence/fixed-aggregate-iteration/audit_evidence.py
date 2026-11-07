"""Read saved artifacts only. No compiler, test, engine, or harness invocation."""
import json, hashlib
from pathlib import Path
P=Path('/tmp/goose-wasm-aggregate-iteration-review-20261107')
S=json.loads((P/'scope.json').read_text()); E=Path(S['evidence_root']); R=Path(S['raw_root']); REPO=Path('/home/dev/Projects/goose-wasm-backend')
A={}; issues=[]
def check(ok,label):
 if not ok:issues.append(label)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for manifest in ['build01/source-hashes.json','full-wasm01/test-hashes.json']:
 m=json.loads((E/manifest).read_text()); bad=[f for f,h in m.items() if not (REPO/f).exists() or digest(REPO/f)!=h]
 A[manifest]={'count':len(m),'mismatches':bad};check(not bad,manifest)
A['parent_compiler_sha256']=digest(Path('/tmp/goose-wasm-fixed-aggregate-arrays-20261107/build02/goose-tested'))
check(A['parent_compiler_sha256']=='bd3856b6c2eedd69bd4eaf343aa9f505794f1a17ab3383194b218fbe33fa368d','parent hash')
A['targeted_records']={}
for unit in ['native01','build01','controls01','controls02']:
 rows=json.loads((E/unit/'results.json').read_text()); bad=[]
 for row in rows:
  name=row['name']; q=E/unit/name
  for ext in ['exit','stdout','stderr']:check(q.with_name(q.name+'.'+ext).exists(),f'{unit}/{name}.{ext} missing')
  if int(q.with_name(q.name+'.exit').read_text())!=row['exit']:bad.append(name)
 A['targeted_records'][unit]={'commands':len(rows),'status_mismatches':bad,'nonzero':[x['name'] for x in rows if x['exit']]};check(not bad,unit+' status mismatch')
A['native_target_comparisons']=[]
for name in json.loads((E/'fixtures.json').read_text()):
 native='build01' if name=='enums' else 'native01'
 for opt in [0,2]:
  stem=f'{name}-O{opt}'; expected=(P/'files/test/expected'/f'wasm_aggregate_iteration_{name}.out').read_bytes()
  for phase in ['native-emit','native-build','native-run']:
   check((E/native/(stem+'-'+phase+'.exit')).read_text().strip()=='0',stem+' '+phase)
  check((E/native/(stem+'-native-run.stdout')).read_bytes()==expected,stem+' native stdout')
  check(not (E/native/(stem+'-native-run.stderr')).read_bytes(),stem+' native stderr')
  check((E/native/(stem+'-prior-wasm.exit')).read_text().strip()=='1',stem+' parent exit')
  check(b'by-value aggregate iteration needs the pending destination lowering' in (E/native/(stem+'-prior-wasm.stderr')).read_bytes(),stem+' parent guard')
  for phase in ['emit','validate','node','wasmtime','owner']:
   check((E/'build01'/(stem+'-'+phase+'.exit')).read_text().strip()=='0',stem+' '+phase)
   check(not (E/'build01'/(stem+'-'+phase+'.stderr')).read_bytes(),stem+' '+phase+' stderr')
   if phase in ['node','wasmtime','owner']:check((E/'build01'/(stem+'-'+phase+'.stdout')).read_bytes()==expected,stem+' '+phase+' stdout')
  A['native_target_comparisons'].append(stem)
A['control_failures']=[]
for opt in [0,2]:
 for kind,line,output in [('short',6,b''),('stride',5,b'iteration\n'),('alias',8,b''),('memory',5,b'')]:
  source=R/('native01/refs_packed.goose' if kind=='memory' else 'controls01/control.goose')
  for engine in ['node','wasmtime']:
   stem=f'{kind}-O{opt}-{engine}'; err=(E/'controls02'/(stem+'.stderr')).read_text()
   check('assert failed' in err and f'{source}:{line}' in err,stem+' failure site')
   check((E/'controls02'/(stem+'.exit')).read_text().strip()=='1',stem+' exit')
   check((E/'controls02'/(stem+'.stdout')).read_bytes()==output,stem+' output')
   A['control_failures'].append({'name':stem,'reason':err.strip()})
 for kind,reason,output in [('long','iteration copy crossed its planned owner image',b''),('eager','zero-trip iteration copied an element',b''),('cleanup','iteration body data top was not restored at its completion',b'inner\n')]:
  stem=f'{kind}-O{opt}-owner';err=(E/'controls02'/(stem+'.stderr')).read_text()
  check(reason in err,stem+' failure reason');check((E/'controls02'/(stem+'.exit')).read_text().strip()=='1',stem+' exit')
  check((E/'controls02'/(stem+'.stdout')).read_bytes()==output,stem+' output')
  A['control_failures'].append({'name':stem,'reason':reason})
 for kind in ['short','stride','alias','memory','long','eager','cleanup']:
  for phase in ['parse','validate']:
   stem=f'{kind}-O{opt}-{phase}'; check((E/'controls02'/(stem+'.exit')).read_text().strip()=='0',stem+' validation')
 stem=f'O{opt}-cleanup-live-owner'
 check((E/'controls02'/(stem+'.exit')).read_text().strip()=='0',stem)
 check(not (E/'controls02'/(stem+'.stderr')).read_bytes(),stem+' stderr')
 check((E/'controls02'/(stem+'.stdout')).read_bytes()==(P/'files/test/expected/wasm_aggregate_iteration_checkpoint.out').read_bytes(),stem+' output')
A['prior_module_pairs']=0
for row in json.loads((E/'compatibility01/prior-modules.json').read_text()):
 stem=f"{Path(row['source']).stem}-O{row['opt']}"; p=R/'compatibility01'
 for ext in ['wasm','stdout','stderr','exit']:
  check((p/(stem+'-before.'+ext)).read_bytes()==(p/(stem+'-after.'+ext)).read_bytes(),stem+' '+ext)
 check(digest(p/(stem+'-before.wasm'))==row['sha256'],stem+' manifest')
 check((p/(stem+'-before.exit')).read_text().strip()=='0',stem+' success')
 A['prior_module_pairs']+=1
A['exact_comparisons']=0
for row in json.loads((E/'compatibility01/exact/summary.json').read_text())['comparisons']:
 stem=f"{Path(row['source']).stem}-{row['target']}-O{row['optimization']}"; p=R/'compatibility01/exact'; ext='c' if row['target']=='native' else 'wasm'
 for suffix in [ext,'stdout','stderr','exit']:
  check((p/(stem+'-reference.'+suffix)).read_bytes()==(p/(stem+'-candidate.'+suffix)).read_bytes(),stem+' '+suffix)
 check(digest(p/(stem+'-candidate.'+ext))==row['output_sha256'],stem+' manifest')
 check((p/(stem+'-candidate.exit')).read_text().strip()=='0',stem+' success')
 A['exact_comparisons']+=1
A['issues']=issues
(P/'review/evidence-audit.json').write_text(json.dumps(A,indent=2)+'\n')
print(json.dumps({k:v for k,v in A.items() if k not in ['targeted_records','native_target_comparisons','control_failures']},indent=2))
print('Compared native/target cases:',len(A['native_target_comparisons']),'Specific control failures:',len(A['control_failures']))
