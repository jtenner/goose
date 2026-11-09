from pathlib import Path
import subprocess,json
raw=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');p=raw/'private01';p.mkdir(exist_ok=True)
commands=[['nice','-n','10','c++','-std=c++20','-O0',str(r/'test/wasm_storage_plan.cpp'),str(r/'build/libgoose_shaderc.a'),'-lm','-pthread','-ldl','-o',str(p/'storage-plan')],[str(p/'storage-plan')]]
for i,args in enumerate(commands):
 a=subprocess.run(args,cwd=r,capture_output=True,timeout=180)
 (p/f'{i}.command.json').write_text(json.dumps(args)+'\n');(p/f'{i}.stdout').write_bytes(a.stdout);(p/f'{i}.stderr').write_bytes(a.stderr);(p/f'{i}.exit').write_text(str(a.returncode)+'\n');assert not a.returncode,(args,a.stderr)
print('PASS symbolic temporary/protected destination and negative binding controls')
