from pathlib import Path
import json,hashlib,re,subprocess
raw=Path(__file__).parent;root=Path('/home/dev/Projects/goose-wasm-backend')
checks=['build03/build','full-correctness02/check','native03/check','compatibility02/check','identity02/check','focused05/check','controls02/check','guards03/check']
for name in checks:
 file=raw/(name+'.exit');assert file.exists() and file.read_text().strip()=='0',(name,file.read_text() if file.exists() else 'missing')
source=json.loads((raw/'build03/source-hashes.json').read_text());inputs=json.loads((raw/'selected-validation-inputs.json').read_text())
for label,manifest in [('source',source),('validation',inputs)]:
 for name,sha in manifest.items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==sha,(label,name)
identity=json.loads((raw/'selected-compiler-identity.json').read_text());assert hashlib.sha256((raw/'build03/goose-tested').read_bytes()).hexdigest()==identity['sha256']
text=(raw/'full-correctness02/check.stdout').read_text();print(text)
record=json.loads((raw/'validation-integrity.json').read_text());record['selected_checks']=checks;record['full_stdout']=text.strip();record['source_parent']=identity['parent'];record['full_memory_matrix_cases']=40;record['status']='PASS'
(raw/'final-validation.json').write_text(json.dumps(record,indent=2)+'\n')
print('PASS all selected checks, compiler identity,',len(source),'source hashes and',len(inputs),'validation input hashes')
