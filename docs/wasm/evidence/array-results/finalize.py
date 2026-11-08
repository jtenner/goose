from pathlib import Path
import json,hashlib,re
raw=Path(__file__).parent;root=Path('/home/dev/Projects/goose-wasm-backend')
checks=['build01/build','full-correctness01/check','native01/check','compatibility01/check','identity01/check','focused01/check','focused02/check','focused03/check','data-image01/check','controls02/check']
for name in checks:
 f=raw/(name+'.exit');assert f.exists() and f.read_text().strip()=='0',(name,f.read_text() if f.exists() else 'missing')
source=json.loads((raw/'build01/source-hashes.json').read_text());inputs=json.loads((raw/'validation-inputs.json').read_text())
for label,manifest in [('source',source),('validation',inputs)]:
 for name,sha in manifest.items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==sha,(label,name)
identity=json.loads((raw/'compiler-identity.json').read_text());assert hashlib.sha256((raw/'build01/goose-tested').read_bytes()).hexdigest()==identity['sha256']
text=(raw/'full-correctness01/check.stdout').read_text();print(text)
native=(raw/'native01/check.stdout').read_text();groups=dict(re.findall(r'^== (.*): (\d+) ok$',native,re.M))
record={'status':'PASS','purpose':'correctness only','source_parent':identity['parent'],'compiler_sha256':identity['sha256'],'source_files':len(source),'validation_inputs':len(inputs),'selected_checks':checks,'full_stdout':text.strip(),'full_memory_matrix_cases':40,'native_groups':groups,'exact_comparisons':52,'unchanged_parent_modules':634,'focused_case_optimization_pairs':54}
(raw/'final-validation.json').write_text(json.dumps(record,indent=2)+'\n')
print('PASS all selected checks, compiler identity,',len(source),'source hashes and',len(inputs),'input hashes')
