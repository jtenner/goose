from pathlib import Path
import shutil,json,hashlib,subprocess
r=Path.cwd();p=Path('/tmp/goose-wasm-array-copy-20261107/final-validation')
for case,name in [('values','wasm_array_copy'),('inline','wasm_array_copy_inline'),('cleanup','wasm_array_copy_cleanup'),('sources','wasm_array_copy_sources')]:
 shutil.copy2(p/(case+'.goose'),r/'test/wasm'/(name+'.goose'))
 (r/'test/expected'/(name+'.out')).write_bytes((p/(case+'-O0-native-run.stdout')).read_bytes())
files=subprocess.check_output(['git','ls-files','src','test','scripts','CMakeLists.txt'],text=True).splitlines()+subprocess.check_output(['git','ls-files','--others','--exclude-standard','test'],text=True).splitlines()
(p/'source-manifest.json').write_text(json.dumps({f:hashlib.sha256((r/f).read_bytes()).hexdigest() for f in sorted(set(files)) if (r/f).is_file()},indent=2)+'\n')
