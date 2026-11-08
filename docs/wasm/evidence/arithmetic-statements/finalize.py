from pathlib import Path
import json,hashlib,subprocess,re
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend')
checks=['build02/check','parent01/check','parent02/check','parent03/check','parent04/check','parent05/check','focused02/check','focused03/check','image01/check','full-correctness01/check','native01/check','exact01/check','identity01/check']
for n in checks:assert (p/(n+'.exit')).read_text().strip()=='0',n
source=json.loads((p/'build02/source-hashes.json').read_text());inputs=json.loads((p/'validation-inputs.json').read_text());identity=json.loads((p/'compiler-identity.json').read_text())
for kind,m in [('source',source),('inputs',inputs)]:
 for n,h in m.items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,(kind,n)
assert hashlib.sha256((p/'build02/goose-tested').read_bytes()).hexdigest()==identity['sha256']
old=Path('/tmp/goose-wasm-fixed-binary-math-20261108');oldidentity=json.loads((old/'compiler-identity.json').read_text());oldsource=json.loads((old/'build01/source-hashes.json').read_text())
assert hashlib.sha256((old/'build01/goose-tested').read_bytes()).hexdigest()==oldidentity['sha256']
for n,h in oldsource.items():assert hashlib.sha256(subprocess.check_output(['git','show',identity['parent']+':'+n],cwd=r)).hexdigest()==h,n
changed=[n for n,h in source.items() if oldsource[n]!=h];assert changed==['src/wasm_codegen.h','src/wasm_fixed.h'],changed
(p/'parent-compiler-identity.json').write_text(json.dumps({'source_commit':identity['parent'],'compiler_sha256':oldidentity['sha256'],'source_hashes_match_commit':len(oldsource),'changed_candidate_source':changed},indent=2)+'\n')
assert (p/'full-correctness01/check.stdout').read_text().strip()=='wasm backend: 4047 checks passed'
native=(p/'native01/check.stdout').read_text();assert 'all tests passed' in native;groups=dict(re.findall(r'^== (.*): (\d+) ok$',native,re.M));assert len(groups)==18
rows=[]
for stage in ['focused02','focused03']:rows+=json.loads((p/stage/'results.json').read_text())
assert len(rows)==58 and len({x['case'] for x in rows})==29
for x in rows:
 n='test/wasm/'+x['case']+'.goose';assert x['source_sha256']==inputs[n],n
modules=json.loads((p/'identity01/results.json').read_text());assert len(modules)==970
images=json.loads((p/'image01/results.json').read_text());assert [x['checks'] for x in images]==[30,4,8,4,12]
parents=[]
for stage in ['parent01','parent02','parent03','parent04','parent05']:parents+=json.loads((p/stage/'results.json').read_text())
valid=[x for x in parents if x.get('native')=='PASS'];assert len(valid)==22
neg=Path('/tmp/goose-wasm-negation-discard-20261108/parent01');assert (neg/'check.exit').read_text().strip()=='0';assert len([x for x in json.loads((neg/'results.json').read_text()) if x.get('native')=='PASS'])==3
assert (p/'build01/operator-guard.exit').read_text().strip()=='1'
assert b'compound arithmetic needs a numeric struct or fixed array' in (p/'build01/operator-guard.stderr').read_bytes()
assert (p/'exact01/check.stdout').read_text().strip()=='shared backend services: 52 exact output and diagnostic comparisons passed'
record={'status':'PASS','purpose':'correctness only','source_parent':identity['parent'],'compiler_sha256':identity['sha256'],'source_files':len(source),'validation_inputs':len(inputs),'changed_source':changed,'selected_checks':checks,'native_valid_parent_compound_failures':22,'native_valid_parent_discard_failures':3,'positive_families':29,'positive_optimization_pairs':58,'observer_and_control_checks':58,'wasm_checks':4047,'unchanged_parent_modules':970,'native_groups':groups,'exact_comparisons':52,'preserved_failures':['joined &= reference token','signed literals for unsigned array compound op','direct call used as assignable receiver','prototype rejected normalized operators','global array checked as a local data owner'],'no_performance_measurements':True}
(p/'final-validation.json').write_text(json.dumps(record,indent=2)+'\n');print('PASS source',len(source),'inputs',len(inputs),'all selected results and hashes')
