from pathlib import Path
import json,hashlib,re
raw=Path(__file__).parent;root=Path('/home/dev/Projects/goose-wasm-backend')
checks=['build02/build','focused02/check','full-correctness01/check','native01/check','compatibility01/check','identity01/check']
for name in checks:
 f=raw/(name+'.exit');assert f.exists() and f.read_text().strip()=='0',(name,f.read_text() if f.exists() else 'missing')
source=json.loads((raw/'build02/source-hashes.json').read_text());inputs=json.loads((raw/'validation-inputs.json').read_text())
for label,manifest in [('source',source),('validation',inputs)]:
 for name,sha in manifest.items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==sha,(label,name)
identity=json.loads((raw/'compiler-identity.json').read_text());assert hashlib.sha256((raw/'build02/goose-tested').read_bytes()).hexdigest()==identity['sha256']
text=(raw/'full-correctness01/check.stdout').read_text();assert 'checks passed' in text;print(text)
native=(raw/'native01/check.stdout').read_text();groups=dict(re.findall(r'^== (.*): (\d+) ok$',native,re.M));assert len(groups)==18
summary=json.loads((raw/'focused02/summary.json').read_text());assert summary=={'pairs':62,'images':8,'guards':4}
record={'status':'PASS','purpose':'correctness only','source_parent':identity['parent'],'compiler_sha256':identity['sha256'],'source_files':len(source),'validation_inputs':len(inputs),'selected_checks':checks,'full_stdout':text.strip(),'full_memory_matrix_cases':40,'native_groups':groups,'exact_comparisons':52,'unchanged_parent_modules':736,'focused_case_optimization_pairs':62,'live_image_checks_and_controls':8,'native_valid_slice_guards':4,'preserved_failures':['parent-extra01','helper-setup-failure01.json','focused01'],'warning_marker_equivalence':'warning02/results.json'}
(raw/'final-validation.json').write_text(json.dumps(record,indent=2)+'\n');print('PASS selected checks and all frozen hashes')
