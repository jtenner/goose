from pathlib import Path
import json,hashlib,subprocess,re
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend')
checks=['build01/check','focused02/check','image01/check','assert-build01/check','assertions01/check','parent-proof01/check','full-correctness01/check','native01/check','exact01/check','identity01/check','sum01/check']
for n in checks:assert (p/(n+'.exit')).read_text().strip()=='0',n
assert (p/'focused01/check.exit').read_text().strip()=='1'
assert b'compound array elements need the pending layout lowering' in (p/'focused01/check.stderr').read_bytes()
source=json.loads((p/'build01/source-hashes.json').read_text());inputs=json.loads((p/'validation-inputs.json').read_text());identity=json.loads((p/'compiler-identity.json').read_text())
for kind,m in [('source',source),('inputs',inputs)]:
 for n,h in m.items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,(kind,n)
assert hashlib.sha256((p/'build01/goose-tested').read_bytes()).hexdigest()==identity['sha256']
assertsource=json.loads((p/'assert-build01/source-hashes.json').read_text());assert assertsource==source
assertidentity=json.loads((p/'assert-build01/compiler-identity.json').read_text());assert assertidentity['cpp_assertions_enabled']
assert hashlib.sha256((p/'assert-build01/goose-tested').read_bytes()).hexdigest()==assertidentity['sha256']
assert '-DNDEBUG' not in (p/'assert-build01/compiler-flags.txt').read_text()
old=Path('/tmp/goose-wasm-array-expression-source-20261108');oldidentity=json.loads((old/'compiler-identity.json').read_text());oldsource=json.loads((old/'build01/source-hashes.json').read_text())
assert hashlib.sha256((old/'build01/goose-tested').read_bytes()).hexdigest()==oldidentity['sha256']
for n,h in oldsource.items():assert hashlib.sha256(subprocess.check_output(['git','show',identity['parent']+':'+n],cwd=r)).hexdigest()==h,n
assert set(source)==set(oldsource)
changed=[n for n,h in source.items() if oldsource[n]!=h];assert set(changed)=={'src/wasm_arrays.h','src/wasm_codegen.h'},changed
(p/'parent-source-verification.json').write_text(json.dumps({'source_commit':identity['parent'],'compiler_sha256':oldidentity['sha256'],'source_hashes_match_commit':len(oldsource),'changed_candidate_source':changed},indent=2)+'\n')
assert (p/'full-correctness01/check.stdout').read_text().strip()=='wasm backend: 6199 checks passed'
native=(p/'native01/check.stdout').read_text();assert 'all tests passed' in native;groups=dict(re.findall(r'^== (.*): (\d+) ok$',native,re.M));assert len(groups)==18
rows=[]
for phase in ['focused02']:rows+=json.loads((p/phase/'results.json').read_text())
assert len(rows)==92 and len({x['case'] for x in rows})==46
for x in rows:
 n='test/wasm/'+x['case']+'.goose';assert x['source_sha256']==inputs[n],n
assertrows=json.loads((p/'assertions01/results.json').read_text());assert len(assertrows)==92
expected={(x['case'],x['opt']):x['wasm_sha256'] for x in rows}
for x in assertrows:assert expected[x['case'],x['opt']]==x['sha256']
modules=json.loads((p/'identity01/results.json').read_text());assert len(modules)==1500
proof=json.loads((p/'parent-verification.json').read_text());assert proof['status']=='PASS' and len(proof['families'])==46
assert (p/'image01/check.stdout').read_text().strip()=='PASS 90 image/control/guard checks'
assert (p/'exact01/check.stdout').read_text().strip()=='shared backend services: 52 exact output and diagnostic comparisons passed'
extra=json.loads((p/'sum01/results.json').read_text());assert len(extra)==2 and {x['opt'] for x in extra}=={0,2}
for n,h in json.loads((p/'sum01/helper-input-hashes.json').read_text()).items():assert inputs[n]==h,n
record={'status':'PASS','purpose':'correctness only','source_parent':identity['parent'],'compiler_sha256':identity['sha256'],'assertion_compiler_sha256':assertidentity['sha256'],'assertion_pairs_and_release_byte_identities':92,'source_files':len(source),'validation_inputs':len(inputs),'changed_source':changed,'selected_checks':checks,'native_valid_parent_failures':46,'positive_families':46,'positive_optimization_pairs':92,'observer_and_control_checks':90,'wasm_checks':6199,'unchanged_parent_modules':1500,'native_groups':groups,'exact_comparisons':52,'raw_u64_receiver_pairs':2,'raw_sum_damaged_count_checks':2,'raw_sum_guard_controls':2,'preserved_scope_failure':'first focused run reached padded nominal array with unsupported non-u32 prefix; exact rejection retained separately','known_remaining_probe_failures':['non-u32 aggregate prefix layouts','growable and runtime-limited sources','nonfixed value calls'],'no_performance_measurements':True}
(p/'final-validation.json').write_text(json.dumps(record,indent=2)+'\n');print('PASS source',len(source),'inputs',len(inputs),'all selected results and hashes')
