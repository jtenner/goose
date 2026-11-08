from pathlib import Path
import json,hashlib,re
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend')
checks=['build01/build','parent-first01/check','matrix-parent01/check','matrix-after01/check','regressions-before01/check','parent-validity01/check','regressions-after01/check','native01/check','exact01/check','full-correctness01/check','identity01/check']
for n in checks:assert (p/(n+'.exit')).read_text().strip()=='0',n
source=json.loads((p/'build01/source-hashes.json').read_text());inputs=json.loads((p/'validation-inputs.json').read_text())
for label,manifest in [('source',source),('inputs',inputs)]:
 for name,sha in manifest.items():assert hashlib.sha256((r/name).read_bytes()).hexdigest()==sha,(label,name)
identity=json.loads((p/'compiler-identity.json').read_text());assert hashlib.sha256((p/'build01/goose-tested').read_bytes()).hexdigest()==identity['sha256']
assert (p/'full-correctness01/check.stdout').read_text().strip()=='wasm backend: 3359 checks passed'
native=(p/'native01/check.stdout').read_text();assert 'all tests passed' in native
groups=dict(re.findall(r'^== (.*): (\d+) ok$',native,re.M));assert len(groups)==18,groups
modules=json.loads((p/'identity01/results.json').read_text());assert len(modules)==848,len(modules)
record={'status':'PASS','purpose':'correctness only','source_parent':identity['parent'],'compiler_sha256':identity['sha256'],'source_files':len(source),'validation_inputs':len(inputs),'selected_checks':checks,'native_groups':groups,'wasm_checks':3359,'unchanged_wasm_modules':len(modules),'exact_native_comparisons':52,'parent_matrix':{'cases':44,'assertion_failures':27,'c_emission_crashes':16,'healthy_alias':1},'candidate_matrix':44,'permanent_regression_runs':12,'parent_frontend_valid_inputs':47,'diagnostic_limit':'sanitizer-before01 expected an OOB diagnostic but reached the known runtime assertion; retained as a failed diagnostic helper, not successful sanitizer evidence'}
(p/'final-validation.json').write_text(json.dumps(record,indent=2)+'\n');print('PASS frozen source',len(source),'inputs',len(inputs),'modules',len(modules))
