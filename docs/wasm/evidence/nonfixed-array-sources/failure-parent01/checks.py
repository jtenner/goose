from pathlib import Path
import json,subprocess,sys
p=Path(__file__).parent;raw=p.parent;r=Path('/home/dev/Projects/goose-wasm-backend');sys.path.insert(0,str(r/'test'))
from wasm_nonfixed_source_checks import range_program
exe=Path(json.loads((raw/'parent-compiler-identity.json').read_text())['compiler']);rows=[];i=0
def run(args):
 global i
 i+=1;args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120)
 (p/f'command-{i:03}.json').write_text(json.dumps(args)+'\n')
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/f'command-{i:03}.{k}').write_bytes(v)
 return a
for kind in ['grow','runtime']:
 source=p/(kind+'.goose');source.write_text(range_program(kind))
 for opt in (0,2):
  stem=p/(kind+f'-O{opt}');c,native,module=[stem.with_suffix(ext) for ext in ['.c','.native','.wasm']]
  a=run([exe,f'-O{opt}','--standalone','-o',c,source]);assert not a.returncode,a.stderr
  a=run(['cc',c,'-pthread','-lm','-ldl','-o',native]);assert not a.returncode,a.stderr
  a=run([native]);assert a.returncode and a.stdout==b'before\n' and b'array length exceeds storage range' in a.stderr,a.stderr
  a=run([exe,f'-O{opt}','--target','wasm','-o',module,source]);assert a.returncode==1 and b'array adaptation needs the pending destination lowering' in a.stderr and not module.exists(),a.stderr
  rows.append({'source':kind,'opt':opt,'status':'PASS native specific runtime range failure; parent Wasm missing conversion'})
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS',len(rows),'native-valid intended range failures and parent conversion rejections')
