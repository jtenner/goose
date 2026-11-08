from pathlib import Path
import json,hashlib,subprocess,re
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend')
checks=['build01/build','parent05-audit/check','focused01/check','focused02/check','focused04/check','image01/check','guards01/check','shape01/check','full-correctness01/check','native01/check','exact01/check','identity01/check']
for n in checks:assert (p/(n+'.exit')).read_text().strip()=='0',n
source=json.loads((p/'build01/source-hashes.json').read_text());inputs=json.loads((p/'validation-inputs.json').read_text());identity=json.loads((p/'compiler-identity.json').read_text())
for kind,m in [('source',source),('inputs',inputs)]:
 for n,h in m.items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,(kind,n)
assert hashlib.sha256((p/'build01/goose-tested').read_bytes()).hexdigest()==identity['sha256']
old=Path('/tmp/goose-native-math-adaptation-20261108');oldidentity=json.loads((old/'compiler-identity.json').read_text());oldsource=json.loads((old/'build01/source-hashes.json').read_text())
assert hashlib.sha256((old/'build01/goose-tested').read_bytes()).hexdigest()==oldidentity['sha256']
for n,h in oldsource.items():assert hashlib.sha256(subprocess.check_output(['git','show',identity['parent']+':'+n],cwd=r)).hexdigest()==h,n
changed=[n for n,h in source.items() if oldsource[n]!=h];assert changed==['src/wasm_fixed.h'],changed
(p/'parent-compiler-identity.json').write_text(json.dumps({'source_commit':identity['parent'],'compiler_sha256':oldidentity['sha256'],'source_hashes_match_commit':len(oldsource),'changed_candidate_source':changed},indent=2)+'\n')
assert (p/'full-correctness01/check.stdout').read_text().strip()=='wasm backend: 3543 checks passed'
native=(p/'native01/check.stdout').read_text();assert 'all tests passed' in native;groups=dict(re.findall(r'^== (.*): (\d+) ok$',native,re.M));assert len(groups)==18
rows=[]
for stage in ['focused01','focused02','focused04']:rows+=json.loads((p/stage/'results.json').read_text())
assert len(rows)==46 and len({x['case'] for x in rows})==23
for x in rows:
 n='test/wasm/wasm_fixed_negation_adapt_'+x['case']+'.goose';assert x['source_sha256']==inputs[n],n
modules=json.loads((p/'identity01/results.json').read_text());assert len(modules)==848
images=json.loads((p/'image01/results.json').read_text());assert [x['checks'] for x in images]==[26,16,4]
record={'status':'PASS','purpose':'correctness only','source_parent':identity['parent'],'compiler_sha256':identity['sha256'],'source_files':len(source),'validation_inputs':len(inputs),'changed_source':changed,'selected_checks':checks,'positive_families':23,'positive_optimization_pairs':46,'node_image_and_control_checks':42,'live_loop_checks_and_controls':4,'inherited_guard_checks':6,'wasm_checks':3543,'unchanged_parent_modules':848,'native_groups':groups,'exact_comparisons':52,'preserved_preparation_failures':['parent01 mixed numeric struct','parent02/03/04 guard classification assertions','focused03 forbidden recursive nonfixed owner'],'no_performance_measurements':True}
(p/'final-validation.json').write_text(json.dumps(record,indent=2)+'\n');print('PASS source',len(source),'inputs',len(inputs),'all selected results and hashes')
(p/'bug-search-report.md').write_text('''# Read-only native Codex bug search\n\nNo confirmed defect found in new ConstructFixed negation adaptation. Count/capacity, prefix width, complete child span, memory identity, zero image and operand lifetime were inspected. Suggested count-width transitions, incoming results, data children, padding, inactive capacity, exits and aliases were covered. Protected assignment retains its complete-RHS image copy, so inactive bytes may differ from a direct native limited-array copy. Spec9.4 permits changed stale limited-array references of the correct type. No unchanged-byte claim applies to inactive assignment slots. No worker writes, builds, tests or timings.\n''')
