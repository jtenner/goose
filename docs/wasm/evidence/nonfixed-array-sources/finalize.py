from pathlib import Path
import json,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend')
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
checks=['build01','parent03','parent04','parent05','parent06','parent07','parent08','parent09','failure-parent01','parent-proof01','focused02','focused03','focused04','focused05','focused06','focused07','images01','images02','images04','assert-build01','assert-check01','identity01','exact01','full-correctness01']
for n in checks:assert (p/n/'check.exit').read_text().strip()=='0',n
for n in ['parent02','focused01','images03']:assert (p/n/'check.exit').read_text().strip()!='0',n
source=json.loads((p/'build01/source-hashes.json').read_text());inputs=json.loads((p/'validation-inputs.json').read_text());identity=json.loads((p/'compiler-identity.json').read_text());old=Path('/tmp/goose-wasm-aggregate-prefix-20261108');oldsource=json.loads((old/'build02/source-hashes.json').read_text())
for n,h in {**source,**inputs}.items():assert sha(r/n)==h,n
assert len(source)==85 and len(inputs)==5967
changed=[n for n,h in source.items() if oldsource[n]!=h];assert changed==['src/wasm_arrays.h'],changed
assert sha(identity['compiler'])==identity['sha256'];assertsource=json.loads((p/'assert-build01/source-hashes.json').read_text());assert assertsource==source
assertidentity=json.loads((p/'assert-build01/compiler-identity.json').read_text());assert assertidentity['cpp_assertions_enabled'] and '-DNDEBUG' not in (p/'assert-build01/compiler-flags.txt').read_text();assert sha(p/'assert-build01/goose-tested')==assertidentity['sha256']
parent=json.loads((p/'parent-verification.json').read_text());assert parent['status']=='PASS' and parent['native_valid_compile_failures']==67
rows=[]
for phase in ['focused02','focused03','focused04','focused05','focused06','focused07']:rows+=json.loads((p/phase/'results.json').read_text())
assert len(rows)==138 and len({x['case'] for x in rows})==69
expected={(x['case'],x['opt']):x['wasm_sha256'] for x in rows}
for x in rows:assert inputs['test/wasm/'+x['case']+'.goose']==x['source_sha256']
assertrows=json.loads((p/'assert-check01/results.json').read_text());assert len(assertrows)==138
for x in assertrows:assert expected[Path(x['source']).stem,x['opt']]==x['sha256']
modules=json.loads((p/'identity01/results.json').read_text());assert len(modules)==1754 and all(x['status']=='identical' for x in modules)
assert (p/'images01/check.stdout').read_text().strip()=='PASS 108 full-image and retained-guard checks'
assert (p/'images02/check.stdout').read_text().strip()=='PASS 12 dynamic full-image and precise control checks'
assert (p/'images04/check.stdout').read_text().strip()=='PASS 16 specific range/product/sum guard checks'
assert (p/'exact01/check.stdout').read_text().strip()=='shared backend services: 52 exact output and diagnostic comparisons passed'
assert (p/'full-correctness01/check.stdout').read_text().strip().endswith('wasm backend: 7279 checks passed')
reuse=json.loads((p/'full-correctness01/fixture-reuse.json').read_text());assert reuse['status']=='PASS verified fixture reuse; fresh core and all suffix checks passed' and reuse['fixture_pairs']==1892
record={'status':'PASS','purpose':'correctness only','source_parent':identity['parent'],'compiler_sha256':identity['sha256'],'assertion_compiler_sha256':assertidentity['sha256'],'source_files':len(source),'validation_inputs':len(inputs),'changed_source':changed,'selected_checks':checks,'native_valid_parent_compile_failures':67,'parent_supported_regression_families':2,'native_valid_specific_range_failure_pairs':4,'positive_families':69,'positive_native_node_wasmtime_and_completed_owner_pairs':138,'assertion_compiler_node_pairs_and_release_byte_identities':138,'new_image_and_specific_guard_checks':136,'wasm_checks':7279,'total_fixture_pairs':1892,'byte_identical_old_fixture_modules':1754,'full_suite_basis':'current core/runtime/layout and every suffix helper execute afresh; executed parent fixtures reused only after current re-emission byte identity; new fixtures execute native/Node/Wasmtime/owner checks afresh','native_baseline':'preceding af5cc6b8 checkpoint full18-group native baseline reused; this delta changes one private Wasm function only; current new native differentials and52 exact native/Wasm comparisons pass','exact_comparisons':52,'no_measurements_timing_profiling':True,'malformed_header_limits':'corrupt-memory product/sum overflow tests are not native-valid source values and do not establish terminal-trap unwind or reentry','preserved_failures':['invalid original recursive source retained a nonfixed owner over recursion','focused01 setup insertion error before producer','images03 sum-control regex selected a later index guard'],'remaining_compile_limits':['nonfixed value transport and fields','aggregate LEB prefixes and data fills','growable-owner reference elements and general compound elements','slices relative references pools native adapters and workers']}
(p/'final-validation.json').write_text(json.dumps(record,indent=2)+'\n');print('PASS source',len(source),'inputs',len(inputs),'Wasm7279 selected checks and frozen identities')
