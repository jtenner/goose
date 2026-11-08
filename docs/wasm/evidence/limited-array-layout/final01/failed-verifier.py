from pathlib import Path
import json,hashlib,subprocess,re
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend')
checks=['build02/check','focused01/check','focused02/check','focused03/check','focused05/check','image03/check','reason02/check','parent-proof01/check','full-correctness02/check','native02/check','exact02/check','identity01/check']
for n in checks:assert (p/(n+'.exit')).read_text().strip()=='0',n
assert (p/'image03/check.stdout').read_text().strip()=='PASS 32 image/control checks'
assert (p/'reason01/check.exit').read_text().strip()=='1'
assert (p/'full-correctness01/check.exit').read_text().strip()=='-2'
source=json.loads((p/'build02/source-hashes.json').read_text());inputs=json.loads((p/'validation-inputs.json').read_text());identity=json.loads((p/'compiler-identity.json').read_text())
for kind,m in [('source',source),('inputs',inputs)]:
 for n,h in m.items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,(kind,n)
assert hashlib.sha256((p/'build02/goose-tested').read_bytes()).hexdigest()==identity['sha256']
old=Path('/tmp/goose-wasm-fixed-array-assignment-layout-20261108');oldidentity=json.loads((old/'compiler-identity.json').read_text());oldsource=json.loads((old/'build01/source-hashes.json').read_text())
assert hashlib.sha256((old/'build01/goose-tested').read_bytes()).hexdigest()==oldidentity['sha256']
for n,h in oldsource.items():assert hashlib.sha256(subprocess.check_output(['git','show',identity['parent']+':'+n],cwd=r)).hexdigest()==h,n
changed=[n for n,h in source.items() if oldsource[n]!=h];assert set(changed)=={'src/wasm_fixed.h','src/wasm_arrays.h','src/wasm_codegen.h'},changed
(p/'parent-source-verification.json').write_text(json.dumps({'source_commit':identity['parent'],'compiler_sha256':oldidentity['sha256'],'source_hashes_match_commit':len(oldsource),'changed_candidate_source':changed},indent=2)+'\n')
assert (p/'full-correctness02/check.stdout').read_text().strip()=='wasm backend: 5223 checks passed'
native=(p/'native02/check.stdout').read_text();assert 'all tests passed' in native;groups=dict(re.findall(r'^== (.*): (\d+) ok$',native,re.M));assert len(groups)==18
rows=json.loads((p/'focused05/results.json').read_text());assert len(rows)==64 and len({x['case'] for x in rows})==32
for x in rows:
 n='test/wasm/'+x['case']+'.goose';assert x['source_sha256']==inputs[n],n
modules=json.loads((p/'identity01/results.json').read_text());assert len(modules)==1266
proof=json.loads((p/'parent-verification.json').read_text());assert proof['status']=='PASS' and len(proof['families'])==32 and len(proof['invalid_fixtures_preserved'])==7
assert (p/'exact02/check.stdout').read_text().strip()=='shared backend services: 52 exact output and diagnostic comparisons passed'
record={'status':'PASS','purpose':'correctness only','source_parent':identity['parent'],'compiler_sha256':identity['sha256'],'source_files':len(source),'validation_inputs':len(inputs),'changed_source':changed,'selected_checks':checks,'native_valid_parent_failures':32,'positive_families':32,'positive_optimization_pairs':64,'observer_and_control_checks':32,'updated_copy_admission_checks':4,'wasm_checks':5223,'unchanged_parent_modules':1266,'native_groups':groups,'exact_comparisons':52,'preserved_invalid_fixture_attempts':7,'corrected_failure_code':'10 array capacity exceeded; initial code 9 pop from empty array and weak filename-matching assertion preserved','interrupted_obsolete_full_suite':'full-correctness01','no_performance_measurements':True}
(p/'final-validation.json').write_text(json.dumps(record,indent=2)+'\n');print('PASS source',len(source),'inputs',len(inputs),'all selected results and hashes')
