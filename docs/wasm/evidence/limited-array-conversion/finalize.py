from pathlib import Path
import json,hashlib,subprocess,re
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend')
checks=['build02/check','runtime-width02/check','focused01/check','focused02/check','image01/check','assert-configure01/check','assert-build01/check','assertions01/check','parent-proof01/check','full-correctness01/check','native01/check','exact01/check','identity01/check']
for n in checks:assert (p/(n+'.exit')).read_text().strip()=='0',n
assert (p/'runtime-width01/check.exit').read_text().strip()=='1'
assert b'array length exceeds stored prefix' in (p/'runtime-width01/command-006.stderr').read_bytes()
source=json.loads((p/'build02/source-hashes.json').read_text());inputs=json.loads((p/'validation-inputs.json').read_text());identity=json.loads((p/'compiler-identity.json').read_text());host=json.loads((p/'build02/host-hashes.json').read_text())
for kind,m in [('source',source),('inputs',inputs),('host',host)]:
 for n,h in m.items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,(kind,n)
assert hashlib.sha256((p/'build02/goose-tested').read_bytes()).hexdigest()==identity['sha256']
assertsource=json.loads((p/'assert-build01/source-hashes.json').read_text());assert assertsource==source
assertidentity=json.loads((p/'assert-build01/compiler-identity.json').read_text());assert assertidentity['cpp_assertions_enabled']
assert hashlib.sha256((p/'assert-build01/goose-tested').read_bytes()).hexdigest()==assertidentity['sha256']
assert '-DNDEBUG' not in (p/'assert-build01/compiler-flags.txt').read_text()
old=Path('/tmp/goose-wasm-limited-array-layout-20261108');oldidentity=json.loads((old/'compiler-identity.json').read_text());oldsource=json.loads((old/'build02/source-hashes.json').read_text())
assert hashlib.sha256((old/'build02/goose-tested').read_bytes()).hexdigest()==oldidentity['sha256']
for n,h in oldsource.items():assert hashlib.sha256(subprocess.check_output(['git','show',identity['parent']+':'+n],cwd=r)).hexdigest()==h,n
assert set(source)==set(oldsource)
changed=[n for n,h in source.items() if oldsource[n]!=h];assert set(changed)=={'src/wasm_arrays.h','src/wasm_codegen.h'},changed
(p/'parent-source-verification.json').write_text(json.dumps({'source_commit':identity['parent'],'compiler_sha256':oldidentity['sha256'],'source_hashes_match_commit':len(oldsource),'changed_candidate_source':changed},indent=2)+'\n')
assert (p/'full-correctness01/check.stdout').read_text().strip()=='wasm backend: 5613 checks passed'
native=(p/'native01/check.stdout').read_text();assert 'all tests passed' in native;groups=dict(re.findall(r'^== (.*): (\d+) ok$',native,re.M));assert len(groups)==18
rows=[]
for phase in ['focused01','focused02']:rows+=json.loads((p/phase/'results.json').read_text())
assert len(rows)==110 and len({x['case'] for x in rows})==55
for x in rows:
 n='test/wasm/'+x['case']+'.goose';assert x['source_sha256']==inputs[n],n
assertrows=json.loads((p/'assertions01/results.json').read_text());assert len(assertrows)==110
expected={(x['case'],x['opt']):x['wasm_sha256'] for x in rows}
for x in assertrows:assert expected[x['case'],x['opt']]==x['sha256']
modules=json.loads((p/'identity01/results.json').read_text());assert len(modules)==1330
proof=json.loads((p/'parent-verification.json').read_text());assert proof['status']=='PASS' and len(proof['families'])==55
assert (p/'image01/check.stdout').read_text().strip()=='PASS 60 image/control checks'
assert (p/'exact01/check.stdout').read_text().strip()=='shared backend services: 52 exact output and diagnostic comparisons passed'
record={'status':'PASS','purpose':'correctness only','source_parent':identity['parent'],'compiler_sha256':identity['sha256'],'assertion_compiler_sha256':assertidentity['sha256'],'assertion_pairs_and_release_byte_identities':110,'source_files':len(source),'host_files':len(host),'validation_inputs':len(inputs),'changed_source':changed,'selected_checks':checks,'native_valid_parent_failures':55,'positive_families':55,'positive_optimization_pairs':110,'observer_and_control_checks':60,'wasm_checks':5613,'unchanged_parent_modules':1330,'native_groups':groups,'exact_comparisons':52,'preserved_prototype_failure':'LenStore called on runtime-limited destination, false 255 limit; exact 256 test fails before fix and passes after','known_remaining_probe_failures':['general block result conversion','non-inlined conditional result conversion'],'no_performance_measurements':True}
(p/'final-validation.json').write_text(json.dumps(record,indent=2)+'\n');print('PASS source',len(source),'inputs',len(inputs),'all selected results and hashes')
