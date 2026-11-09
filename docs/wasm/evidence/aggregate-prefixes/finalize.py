from pathlib import Path
import json,hashlib,subprocess,re
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend')
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
checks=['build02/check','focused03/check','focused04/check','focused05/check','image05/check','construction-model01/check','nested-data-model01/check','assert-build02/check','assertions02/check','parent-proof01/check','parent-proof02/check','full-correctness07/check','native01/check','exact01/check','identity01/check','count02/check']
for n in checks:assert (p/(n+'.exit')).read_text().strip()=='0',n
for n in ['image01','image02','image03','image04','full-correctness01','full-correctness02','full-correctness03','full-correctness04','full-correctness05','full-correctness06','count01']:assert (p/n/'check.exit').read_text().strip()!='0',n
source=json.loads((p/'build02/source-hashes.json').read_text());inputs=json.loads((p/'validation-inputs.json').read_text());identity=json.loads((p/'compiler-identity.json').read_text())
for kind,m in [('source',source),('inputs',inputs)]:
 for n,h in m.items():assert sha(r/n)==h,(kind,n)
assert sha(p/'build02/goose-tested')==identity['sha256']
assert json.loads((p/'assert-build02/source-hashes.json').read_text())==source
assertidentity=json.loads((p/'assert-build02/compiler-identity.json').read_text());assert assertidentity['cpp_assertions_enabled']
assert sha(p/'assert-build02/goose-tested')==assertidentity['sha256']
assert '-DNDEBUG' not in (p/'assert-build02/compiler-flags.txt').read_text()
parent=json.loads((p/'parent-verification.json').read_text());assert parent['status']=='PASS'
old=Path('/tmp/goose-wasm-array-prefix-conversion-20261108');oldsource=json.loads((old/'build01/source-hashes.json').read_text())
changed=[n for n,h in source.items() if oldsource[n]!=h]
assert set(changed)=={'src/wasm_arrays.h','src/wasm_codegen.h','src/wasm_fixed.h','src/wasm_support.h'},changed
assert (p/'full-correctness07/check.stdout').read_text().strip().endswith('wasm backend: 6729 checks passed')
reuse=json.loads((p/'full-correctness07/prefix-reuse.json').read_text());assert reuse['status']=='PASS completed prefix verified; all later checks passed' and reuse['fixture_pairs']==1754
native=(p/'native01/check.stdout').read_text();assert 'all tests passed' in native;groups=dict(re.findall(r'^== (.*): (\d+) ok$',native,re.M));assert len(groups)==18
assert groups['parse, roundtrip and typecheck']=='3262' and groups['generated C, built and run at -O0 and -O2']=='1607' and groups['JIT (TinyCC) runs']=='1782'
rows=[]
for phase in ['focused03','focused04','focused05']:rows+=json.loads((p/phase/'results.json').read_text())
assert len(rows)==154 and len({x['case'] for x in rows})==77
for x in rows:
 n='test/wasm/'+x['case']+'.goose';assert x['source_sha256']==inputs[n],n
assertrows=json.loads((p/'assertions02/results.json').read_text());assert len(assertrows)==154
expected={(x['case'],x['opt']):x['wasm_sha256'] for x in rows}
for x in assertrows:assert expected[x['case'],x['opt']]==x['sha256']
modules=json.loads((p/'identity01/results.json').read_text());assert len(modules)==1592
assert (p/'image05/check.stdout').read_text().strip()=='PASS 64 image/identity/cleanup/guard checks'
assert (p/'exact01/check.stdout').read_text().strip()=='shared backend services: 52 exact output and diagnostic comparisons passed'
record={'status':'PASS','purpose':'correctness only','source_parent':identity['parent'],'compiler_sha256':identity['sha256'],'assertion_compiler_sha256':assertidentity['sha256'],'assertion_pairs_and_release_byte_identities':154,'source_files':len(source),'validation_inputs':len(inputs),'changed_source':changed,'selected_checks':checks,'native_valid_parent_compile_failures':58,'native_valid_parent_wrong_results':17,'stored_copy_regressions':1,'dynamic_parent_active_values_pass_and_dirty_image_fails':True,'positive_families':77,'positive_optimization_pairs':154,'observer_and_control_checks':64,'wasm_checks':6729,'full_suite_phases':['full-correctness03 completed core/fixture phase','full-correctness07 verified prefix reuse and reran every later helper'],'parent_modules':1592,'unchanged_parent_modules':sum(x['status']=='identical' for x in modules),'parent_modules_with_new_suffix_clear':sum(x['status']!='identical' for x in modules),'native_groups':groups,'exact_comparisons':52,'frontend_count256_rejection_checks':4,'preserved_failures':['header-store alignment and fill helper-name assumptions','empty struct and zero-length field invalid zero-stride test assumptions','old C++ fixed-prefix admission expectation','count256 already rejected by frontend','older aggregate fill image expected poison in freshly constructed unused slots','continuation setup omitted a bound comprehension name'],'known_remaining_compile_limits':['aggregate LEB prefixes and data fills','growable and runtime-limited source conversions','nonfixed value calls and fields'],'interrupted_full_run':'full-correctness02 stopped and all owned processes exited for owner profiling hold; full-correctness03 completed every fixture; a stale observer was corrected and every later helper ran in full-correctness07','no_performance_measurements':True}
(p/'final-validation.json').write_text(json.dumps(record,indent=2)+'\n');print('PASS source',len(source),'inputs',len(inputs),'all selected results and hashes')
