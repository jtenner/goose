from pathlib import Path
import json,hashlib,subprocess,re
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend')
checks=['build01/check','parent01-verify/check','parent02/check','parent03/check','parent04/check','parent05/check','focused02/check','focused03/check','focused04/check','admission01/check','admission03/check','image03/check','full-correctness02/check','native02/check','exact01/check','identity01/check']
for n in checks:assert (p/(n+'.exit')).read_text().strip()=='0',n
for failed in ['focused01','image01','image02','admission02','full-correctness01']:assert (p/failed/'check.exit').read_text().strip()=='1'
assert [x['checks'] for x in json.loads((p/'image03/results.json').read_text())]==[20,12]
source=json.loads((p/'build01/source-hashes.json').read_text());inputs=json.loads((p/'validation-inputs.json').read_text());identity=json.loads((p/'compiler-identity.json').read_text())
for kind,m in [('source',source),('inputs',inputs)]:
 for n,h in m.items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,(kind,n)
assert hashlib.sha256((p/'build01/goose-tested').read_bytes()).hexdigest()==identity['sha256']
old=Path('/tmp/goose-wasm-array-math-destinations-20261108');oldidentity=json.loads((old/'compiler-identity.json').read_text());oldsource=json.loads((old/'build01/source-hashes.json').read_text())
assert hashlib.sha256((old/'build01/goose-tested').read_bytes()).hexdigest()==oldidentity['sha256']
for n,h in oldsource.items():assert hashlib.sha256(subprocess.check_output(['git','show',identity['parent']+':'+n],cwd=r)).hexdigest()==h,n
changed=[n for n,h in source.items() if oldsource[n]!=h];assert changed==['src/wasm_arrays.h','src/wasm_codegen.h','src/wasm_fixed.h'],changed
(p/'parent-source-verification.json').write_text(json.dumps({'source_commit':identity['parent'],'compiler_sha256':oldidentity['sha256'],'source_hashes_match_commit':len(oldsource),'changed_candidate_source':changed},indent=2)+'\n')
assert (p/'full-correctness02/check.stdout').read_text().strip()=='wasm backend: 4811 checks passed'
native=(p/'native02/check.stdout').read_text();assert 'all tests passed' in native;groups=dict(re.findall(r'^== (.*): (\d+) ok$',native,re.M));assert len(groups)==18
rows=[]
for phase in ['focused02','focused03','focused04']:rows+=json.loads((p/phase/'results.json').read_text())
assert len(rows)==64 and len({x['case'] for x in rows})==32
for x in rows:
 n='test/wasm/'+x['case']+'.goose';assert x['source_sha256']==inputs[n],n
modules=json.loads((p/'identity01/results.json').read_text());assert len(modules)==1160
initial=json.loads((p/'parent01/results.json').read_text());assert len(initial)==5 and all(x['wasm_exit']==1 and x['native_exit']==0 for x in initial)
parents=[]
for phase in ['parent02','parent03','parent04','parent05']:parents+=json.loads((p/phase/'results.json').read_text())
assert len(parents)==27 and all(x.get('native')=='PASS' for x in parents)
assert sum(bool(x.get('wasm_reason')) for x in parents)==26
assert [x['case'] for x in parents if x.get('wasm')=='already-supported']==['callback']
assert (p/'exact01/check.stdout').read_text().strip()=='shared backend services: 52 exact output and diagnostic comparisons passed'
record={'status':'PASS','purpose':'correctness only','source_parent':identity['parent'],'compiler_sha256':identity['sha256'],'source_files':len(source),'validation_inputs':len(inputs),'changed_source':changed,'selected_checks':checks,'native_valid_parent_failures':31,'parent_supported_regression_families':1,'positive_families':32,'positive_optimization_pairs':64,'observer_and_control_checks':32,'updated_admission_positive_checks':16,'direct_admission_and_retained_limits':26,'wasm_checks':4811,'unchanged_parent_modules':1160,'native_groups':groups,'exact_comparisons':52,'preserved_preparation_failures':['focused owner mode incorrectly required data memory','observer used nonexistent host memory field','long-copy control exposed same-byte poison pattern','old admission guards expected the newly supported rejection','direct aggregate helper argument order'],'no_performance_measurements':True}
(p/'final-validation.json').write_text(json.dumps(record,indent=2)+'\n');print('PASS source',len(source),'inputs',len(inputs),'all selected results and hashes')
