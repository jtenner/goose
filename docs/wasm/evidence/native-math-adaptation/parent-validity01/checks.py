from pathlib import Path
import json,hashlib,subprocess,shutil
p=Path(__file__).parent;r=Path.cwd();exe=Path('/tmp/goose-wasm-fixed-negation-20261108/build01/goose-tested');rows=[]
def run(stem,args):
 a=subprocess.run(list(map(str,args)),capture_output=True,timeout=120)
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(stem+'.'+k)).write_bytes(v)
 return a
sources=list((p.parent/'matrix-parent01').glob('*.goose'))+[r/'test/codegen'/(x+'.goose') for x in ['fixed_math_destinations','fixed_math_lifetimes','fixed_math_capacity']]
for f in sorted(sources):
 copy=p/f.name;shutil.copy2(f,copy)
 a=run(f.stem+'-check',[exe,'--check',copy]);assert not a.returncode,(f,a.stderr)
 row={'source':str(f),'sha256':hashlib.sha256(copy.read_bytes()).hexdigest(),'check_exit':a.returncode}
 if f.stem.startswith('fixed_math_'):
  a=run(f.stem+'-emit',[exe,'-O0','--standalone','-o',p/(f.stem+'.c'),copy]);assert a.returncode==-11,(f,a)
  row['emit_exit']=a.returncode
 rows.append(row)
assert len(rows)==47,len(rows)
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS all47 inputs accepted by parent frontend; all3 final fixtures reproduce C-emission crash')
