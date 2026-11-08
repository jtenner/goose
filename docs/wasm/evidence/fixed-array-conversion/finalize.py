from pathlib import Path
import json,hashlib,subprocess,re
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend')
checks=['build01/check','parent01/check','parent02/check','parent03-audit/check','parent04/check','parent05/check','parent06/check','parent07/check','focused01/check','focused02/check','focused03/check','focused04/check','image02/check','full-correctness01/check','native01/check','exact01/check','identity01/check']
for n in checks:assert (p/(n+'.exit')).read_text().strip()=='0',n
assert (p/'prefix-parent01/0.exit').read_text().strip()=='1'
assert b'array length 256 exceeds storage range of i64[u8]' in (p/'prefix-parent01/0.stderr').read_bytes()
# The first four groups passed before the preserved namespace helper failure.
assert (p/'image01/check.exit').read_text().strip()=='1'
assert [x['checks'] for x in json.loads((p/'image01/results.json').read_text())]==[50,40,10,4]
assert [x['checks'] for x in json.loads((p/'image02/results.json').read_text())]==[4,4]
source=json.loads((p/'build01/source-hashes.json').read_text());inputs=json.loads((p/'validation-inputs.json').read_text());identity=json.loads((p/'compiler-identity.json').read_text())
for kind,m in [('source',source),('inputs',inputs)]:
 for n,h in m.items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,(kind,n)
assert hashlib.sha256((p/'build01/goose-tested').read_bytes()).hexdigest()==identity['sha256']
old=Path('/tmp/goose-wasm-zero-call-20261108');oldidentity=json.loads((old/'compiler-identity.json').read_text());oldsource=json.loads((old/'build01/source-hashes.json').read_text())
assert hashlib.sha256((old/'build01/goose-tested').read_bytes()).hexdigest()==oldidentity['sha256']
for n,h in oldsource.items():assert hashlib.sha256(subprocess.check_output(['git','show',identity['parent']+':'+n],cwd=r)).hexdigest()==h,n
changed=[n for n,h in source.items() if oldsource[n]!=h];assert changed==['src/wasm_arrays.h','src/wasm_codegen.h'],changed
(p/'parent-compiler-identity.json').write_text(json.dumps({'source_commit':identity['parent'],'compiler_sha256':oldidentity['sha256'],'source_hashes_match_commit':len(oldsource),'changed_candidate_source':changed},indent=2)+'\n')
assert (p/'full-correctness01/check.stdout').read_text().strip()=='wasm backend: 4587 checks passed'
native=(p/'native01/check.stdout').read_text();assert 'all tests passed' in native;groups=dict(re.findall(r'^== (.*): (\d+) ok$',native,re.M));assert len(groups)==18
rows=[]
for phase in ['focused01','focused02','focused03','focused04']:rows+=json.loads((p/phase/'results.json').read_text())
assert len(rows)==90 and len({x['case'] for x in rows})==45
for x in rows:
 n='test/wasm/'+x['case']+'.goose';assert x['source_sha256']==inputs[n],n
modules=json.loads((p/'identity01/results.json').read_text());assert len(modules)==1070
parents=[]
for phase in ['parent01','parent02','parent04','parent05','parent06','parent07']:parents+=json.loads((p/phase/'results.json').read_text())
assert len(parents)==45 and all(x.get('native')=='PASS' and x.get('wasm_reason') for x in parents)
assert (p/'exact01/check.stdout').read_text().strip()=='shared backend services: 52 exact output and diagnostic comparisons passed'
record={'status':'PASS','purpose':'correctness only','source_parent':identity['parent'],'compiler_sha256':identity['sha256'],'source_files':len(source),'validation_inputs':len(inputs),'changed_source':changed,'selected_checks':checks,'native_valid_parent_failures':45,'positive_families':45,'positive_optimization_pairs':90,'observer_and_control_checks':112,'unchanged_frontend_prefix_rejection':True,'wasm_checks':4587,'unchanged_parent_modules':1070,'native_groups':groups,'exact_comparisons':52,'preserved_preparation_failures':['namespace observer assumed one generated function and dynamic memory parameter'],'no_performance_measurements':True}
(p/'final-validation.json').write_text(json.dumps(record,indent=2)+'\n');print('PASS source',len(source),'inputs',len(inputs),'all selected results and hashes')
