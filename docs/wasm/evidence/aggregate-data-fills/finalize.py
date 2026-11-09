from pathlib import Path
import json,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend')
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
checks=['parent04','parent05','parent06','parent-proof01','build01','focused01','focused02','images03','assert-build01','assert-check01','identity01','exact01','full-correctness01','parent-limits01','limits01','assert-limits01']
for n in checks:assert (p/n/'check.exit').read_text().strip()=='0',n
for n in ['parent01','parent02','parent03','images01','images02']:assert (p/n/'check.exit').read_text().strip()!='0',n
source=json.loads((p/'build01/source-hashes.json').read_text());inputs=json.loads((p/'validation-inputs.json').read_text());identity=json.loads((p/'compiler-identity.json').read_text());old=Path('/tmp/goose-wasm-nonfixed-source-20261108');oldsource=json.loads((old/'build01/source-hashes.json').read_text())
for n,h in {**source,**inputs}.items():assert sha(r/n)==h,n
assert len(source)==85 and len(inputs)==6055
changed=[n for n,h in source.items() if oldsource[n]!=h];assert changed==['src/wasm_arrays.h'],changed
assert sha(identity['compiler'])==identity['sha256'];assertsource=json.loads((p/'assert-build01/source-hashes.json').read_text());assert assertsource==source
assertidentity=json.loads((p/'assert-build01/compiler-identity.json').read_text());assert assertidentity['cpp_assertions_enabled'] and '-DNDEBUG' not in (p/'assert-build01/compiler-flags.txt').read_text();assert sha(p/'assert-build01/goose-tested')==assertidentity['sha256']
parent=json.loads((p/'parent-verification.json').read_text());assert parent['status']=='PASS' and parent['native_valid_wasm_compile_failures']==43
rows=[]
for phase in ['focused01','focused02']:rows+=json.loads((p/phase/'results.json').read_text())
assert len(rows)==86 and len({x['case'] for x in rows})==43
expected={(x['case'],x['opt']):x['wasm_sha256'] for x in rows}
for x in rows:assert inputs['test/wasm/'+x['case']+'.goose']==x['source_sha256']
assertrows=json.loads((p/'assert-check01/results.json').read_text());assert len(assertrows)==86
for x in assertrows:assert expected[Path(x['source']).stem,x['opt']]==x['sha256']
modules=json.loads((p/'identity01/results.json').read_text());assert len(modules)==1892 and all(x['status']=='identical' for x in modules)
assert (p/'images02/check.stdout').read_text().strip()=='Static 100'
assert (p/'images03/check.stdout').read_text().strip()=='PASS 114 complete fill image/snapshot/identity/cleanup controls; static100 verified reused'
assert json.loads((p/'images03/static-reuse.json').read_text())['status']=='PASS'
assert (p/'exact01/check.stdout').read_text().strip()=='shared backend services: 52 exact output and diagnostic comparisons passed'
assert (p/'full-correctness01/check.stdout').read_text().strip().endswith('wasm backend: 7651 checks passed')
reuse=json.loads((p/'full-correctness01/fixture-reuse.json').read_text());assert reuse['status']=='PASS verified fixture reuse; fresh core and all suffix checks passed' and reuse['fixture_pairs']==1978
assert (p/'limits01/check.stdout').read_text().strip()=='PASS8 memory32 count/extent checks; guarded branch prevents huge fill execution'
assert len(json.loads((p/'parent-limits01/results.json').read_text()))==4
extension=json.loads((p/'count-extension-proof.json').read_text());assert extension['status']=='PASS' and extension['added_limits_checks']==8
original_inputs=json.loads((p/'full-correctness01/validation-inputs.json').read_text())
assert {n for n,h in original_inputs.items() if inputs[n]!=h}==set(extension['changed_inputs'])
assertions=json.loads((p/'assert-limits01/results.json').read_text());assert len(assertions)==8
record={'status':'PASS','purpose':'correctness only','source_parent':identity['parent'],'compiler_sha256':identity['sha256'],'assertion_compiler_sha256':assertidentity['sha256'],'source_files':len(source),'validation_inputs':len(inputs),'changed_source':changed,'selected_checks':checks,'native_valid_parent_compile_failures':43,'positive_families':43,'positive_native_node_wasmtime_completed_owner_pairs':86,'assertion_compiler_node_pairs_and_release_byte_identities':86,'additional_boundary_assertion_compile_checks':8,'new_image_and_fault_control_checks':114,'wasm_checks':7659,'original_full_phase_checks':7651,'additional_count_boundary_checks':8,'total_fixture_pairs':1978,'byte_identical_old_fixture_modules':1892,'full_suite_basis':'7651-check core/runtime/layout and every then-registered suffix helper run fresh; final8 added boundary checks run separately, with exact code-extension proof; executed parent fixture pairs reused after current re-emission byte identity; all new fixtures execute native/Node/Wasmtime/owner checks afresh','native_baseline':'previous full18-group native baseline remains; this delta changes one private Wasm constructor function only;43 current native differential families and52 exact native/Wasm comparisons pass','exact_comparisons':52,'no_measurements_timing_profiling':True,'preserved_setup_failures':['parent01/02/03 source sketch syntax errors; valid producers reused by hash','images01 matching source/destination sentinels masked long-copy control','images02 dynamic control assumed generic copy helper rather than existing CopyFromFrame','registration setup expected parenthesized import; test freeze repaired before checks on unchanged compiler'],'remaining_compile_limits':['aggregate LEB prefixes','nonfixed fields value transport and constructors','nonfixed aggregate elements','relative references slices pools native adapters and workers']}
(p/'final-validation.json').write_text(json.dumps(record,indent=2)+'\n');print('PASS source85 inputs6055 Wasm7659 all selected checks and frozen identities')
