from pathlib import Path
import shutil,json,hashlib,subprocess
r=Path.cwd();p=Path('/tmp/goose-wasm-varint-prefix-20261107')
for case,name in [('values','wasm_varint_prefix'),('paths','wasm_varint_paths'),('bytes','wasm_varint_bytes'),('cleanup','wasm_varint_cleanup')]:
 shutil.copy2(p/(case+'.goose'),r/'test/wasm'/(name+'.goose'))
 (r/'test/expected'/(name+'.out')).write_bytes((p/(case+'-O0-native-run.stdout')).read_bytes())
files=subprocess.check_output(['git','ls-files','src','test','scripts','CMakeLists.txt'],text=True).splitlines()+subprocess.check_output(['git','ls-files','--others','--exclude-standard','test'],text=True).splitlines()
(p/'source-manifest.json').write_text(json.dumps({f:hashlib.sha256((r/f).read_bytes()).hexdigest() for f in sorted(set(files)) if (r/f).is_file()},indent=2)+'\n')
