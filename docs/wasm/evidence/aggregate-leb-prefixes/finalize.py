from pathlib import Path
import json,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend')
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
checks=['parent02','parent03','parent04','parent-proof01','build01','focused01','focused02','large-control01','images02','sizes01','assert-build01','assert-check01','identity01','exact01','admission01','full-correctness03']
for n in checks:assert (p/n/'check.exit').read_text().strip()=='0',n
for n in ['parent01','parent05','images01','full-correctness01','full-correctness02']:assert (p/n/'check.exit').read_text().strip()!='0',n
source=json.loads((p/'build01/source-hashes.json').read_text());inputs=json.loads((p/'validation-inputs.json').read_text());identity=json.loads((p/'compiler-identity.json').read_text());oldsource=json.loads(Path('/tmp/goose-wasm-aggregate-data-fill-20261109/build01/source-hashes.json').read_text())
for n,h in {**source,**inputs}.items():assert sha(r/n)==h,n
assert len(source)==85 and len(inputs)==6125
changed=[n for n,h in source.items() if oldsource[n]!=h];assert set(changed)=={'src/wasm_arrays.h','src/wasm_support.h'},changed
assert sha(identity['compiler'])==identity['sha256'];assertsource=json.loads((p/'assert-build01/source-hashes.json').read_text());assert assertsource==source
assertidentity=json.loads((p/'assert-build01/compiler-identity.json').read_text());assert assertidentity['cpp_assertions_enabled'] and '-DNDEBUG' not in (p/'assert-build01/compiler-flags.txt').read_text();assert sha(p/'assert-build01/goose-tested')==assertidentity['sha256']
parent=json.loads((p/'parent-verification.json').read_text());assert parent['status']=='PASS' and parent['native_valid_wasm_compile_failures']==33
rows=[]
for phase in ['focused01','focused02']:rows+=json.loads((p/phase/'results.json').read_text())
assert len(rows)==66 and len({x['case'] for x in rows})==33
expected={(x['case'],x['opt']):x['wasm_sha256'] for x in rows}
for x in rows:assert inputs['test/wasm/'+x['case']+'.goose']==x['source_sha256']
assertrows=json.loads((p/'assert-check01/results.json').read_text());assert len(assertrows)==66
for x in assertrows:assert expected[Path(x['source']).stem,x['opt']]==x['sha256']
modules=json.loads((p/'identity01/results.json').read_text());assert len(modules)==1978 and all(x['status']=='identical' for x in modules)
assert (p/'images02/check.stdout').read_text().strip().endswith('PASS 126 LEB fill/copy images, precise controls and retained guards')
assert (p/'sizes01/check.stdout').read_text().strip()=='PASS8 LEB product/sum preallocation guards and precise controls'
assert (p/'exact01/check.stdout').read_text().strip()=='shared backend services: 52 exact output and diagnostic comparisons passed'
assert (p/'full-correctness03/check.stdout').read_text().strip().endswith('wasm backend: 7991 checks passed')
reuse=json.loads((p/'full-correctness03/prefix-reuse.json').read_text());assert reuse['status']=='PASS completed prefix verified; all later checks passed' and reuse['fixture_pairs']==2044 and reuse['completed_prefix_checks']==6243
record={'status':'PASS','purpose':'correctness only','source_parent':identity['parent'],'compiler_sha256':identity['sha256'],'assertion_compiler_sha256':assertidentity['sha256'],'source_files':len(source),'validation_inputs':len(inputs),'changed_source':changed,'selected_checks':checks,'native_valid_parent_compile_failures':33,'positive_families':33,'positive_native_node_wasmtime_completed_owner_pairs':66,'assertion_compiler_node_pairs_and_release_byte_identities':66,'image_and_retained_guard_checks':126,'malformed_header_product_and_sum_checks':8,'wasm_checks':7991,'total_fixture_pairs':2044,'byte_identical_old_fixture_modules':1978,'full_suite_basis':'full-correctness01 completed6243 checks including core/runtime/layout then stopped at obsolete data-varint rejection; full-correctness03 verifies that prefix and reruns corrected admission and all later helpers; all current fixture byte hashes verified, all new native/Node/Wasmtime/owner pairs execute','native_baseline':'prior full18-group baseline retained; this delta changes private Wasm headers only;33 current native differential families and52 native/Wasm exact comparisons pass','exact_comparisons':52,'no_measurements_timing_profiling':True,'guarded_large_count_limits':'two cases compile four/five-byte prefix reservation paths behind false runtime flags; large payloads not executed','malformed_header_limits':'controlled memory corruption, not native-valid values; no terminal-trap unwind/reentry claim','preserved_failures':['invalid initial copied-binder syntax,23 valid parent cases reused','empty-variant element rejected by shared frontend; no native runtime claim','large Buffer assertion fault control timed out; concise full-Buffer.equals assertion passes unchanged mutant then full image unit reruns','old aggregate-admission data-varint rejection became supported; now native/Node/Wasmtime/owner positive','full-correctness02 continuation static name check omitted nested function and argument bindings; corrected setup03 ran remaining checks'],'remaining_compile_limits':['aggregate array equality','nonfixed fields value transport and aggregate growable/runtime layouts','relative references slices pools native adapters and workers']}
(p/'final-validation.json').write_text(json.dumps(record,indent=2)+'\n');print('PASS source85 inputs6125 Wasm7991 all selected checks and frozen identities')
