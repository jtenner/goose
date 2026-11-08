from pathlib import Path
import subprocess,json
p=Path(__file__).parent;rows=[]
def run(name,args):
 a=subprocess.run(list(map(str,args)),capture_output=True,timeout=120)
 for ext,b in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]:(p/(name+'.'+ext)).write_bytes(b)
 return a
for name in ['unary_decl','binary_decl']:
 source=p.parent/'parent-first01'/(name+'-O0.c');exe=p/(name+'.native')
 args=['clang','-O1','-fsanitize=undefined','-fno-sanitize-recover=all',source,'-pthread','-lm','-ldl','-o',exe]
 a=run(name+'-cc',args);assert not a.returncode,a.stderr
 a=run(name+'-before',[exe]);assert a.returncode!=0 and b'out of bounds' in a.stderr,(name,a)
 rows.append({'case':name,'compile_args':list(map(str,args)),'exit':a.returncode,'reason':a.stderr.decode()})
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS',len(rows),'specific native OOB sanitizer failures recorded')
