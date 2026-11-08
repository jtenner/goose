from pathlib import Path
import json,hashlib,subprocess,re
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend')
checks=['build01/build','parent01/check','parent02/check','parent03/check','parent04/check','focused01/check','focused02/check','focused03/check','focused04/check','image04/check','full-correctness01/check','native01/check','exact01/check','identity01/check']
for n in checks:assert (p/(n+'.exit')).read_text().strip()=='0',n
source=json.loads((p/'build01/source-hashes.json').read_text());inputs=json.loads((p/'validation-inputs.json').read_text());identity=json.loads((p/'compiler-identity.json').read_text())
for kind,m in [('source',source),('inputs',inputs)]:
 for n,h in m.items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,(kind,n)
assert hashlib.sha256((p/'build01/goose-tested').read_bytes()).hexdigest()==identity['sha256']
old=Path('/tmp/goose-wasm-negation-adaptation-20261108');oldidentity=json.loads((old/'compiler-identity.json').read_text());oldsource=json.loads((old/'build01/source-hashes.json').read_text())
assert hashlib.sha256((old/'build01/goose-tested').read_bytes()).hexdigest()==oldidentity['sha256']
for n,h in oldsource.items():assert hashlib.sha256(subprocess.check_output(['git','show',identity['parent']+':'+n],cwd=r)).hexdigest()==h,n
changed=[n for n,h in source.items() if oldsource[n]!=h];assert changed==['src/wasm_arrays.h','src/wasm_codegen.h','src/wasm_fixed.h'],changed
(p/'parent-compiler-identity.json').write_text(json.dumps({'source_commit':identity['parent'],'compiler_sha256':oldidentity['sha256'],'source_hashes_match_commit':len(oldsource),'changed_candidate_source':changed},indent=2)+'\n')
full=(p/'full-correctness01/check.stdout').read_text().strip();m=re.fullmatch(r'wasm backend: (\d+) checks passed',full);assert m,full;wasm=int(m[1]);assert wasm==3815,wasm
native=(p/'native01/check.stdout').read_text();assert 'all tests passed' in native;groups=dict(re.findall(r'^== (.*): (\d+) ok$',native,re.M));assert len(groups)==18
rows=[]
for stage in ['focused01','focused02','focused03','focused04']:rows+=json.loads((p/stage/'results.json').read_text())
assert len(rows)==76 and len({x['case'] for x in rows})==38
for x in rows:
 n='test/wasm/wasm_fixed_binary_'+x['case']+'.goose';assert x['source_sha256']==inputs[n],n
modules=json.loads((p/'identity01/results.json').read_text());assert len(modules)==894
assert json.loads((p/'image01/results.json').read_text())==[{'name':'images','checks':30}]
assert json.loads((p/'image02/results.json').read_text())==[{'name':'snapshot','checks':4},{'name':'loop','checks':4}]
assert json.loads((p/'image04/results.json').read_text())=={'failures':6}
# Parent02 has one invalid fixed-array .cap fixture. The corrected source ran
# separately in parent03; no invalid case is counted as failing-first evidence.
parents=[]
for stage in ['parent01','parent02','parent03','parent04']:parents+=json.loads((p/stage/'results.json').read_text())
valid=[x for x in parents if x.get('native')=='PASS'];assert len(valid)==35
assert (p/'exact01/check.stdout').read_text().strip()=='shared backend services: 52 exact output and diagnostic comparisons passed'
record={'status':'PASS','purpose':'correctness only','source_parent':identity['parent'],'compiler_sha256':identity['sha256'],'source_files':len(source),'validation_inputs':len(inputs),'changed_source':changed,'selected_checks':checks,'native_valid_parent_failures':len(valid),'positive_families':38,'positive_optimization_pairs':76,'node_image_and_control_checks':30,'ordered_snapshot_checks_and_controls':4,'live_loop_checks_and_controls':4,'trap_atomicity_checks':6,'wasm_checks':wasm,'unchanged_parent_modules':len(modules),'native_groups':groups,'exact_comparisons':52,'preserved_preparation_failures':['parent02 fixed-array .cap admission','image01 missing call-counter expectation','image02 native overflow reason wording','image03 artifact-path identity mismatch'],'no_performance_measurements':True}
(p/'final-validation.json').write_text(json.dumps(record,indent=2)+'\n');print('PASS source',len(source),'inputs',len(inputs),'all selected results and hashes')
