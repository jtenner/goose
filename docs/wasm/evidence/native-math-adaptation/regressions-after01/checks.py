from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');exe=p.parent/'build01/goose-tested';rows=[]
def run(name,args):
 a=subprocess.run(list(map(str,args)),cwd=r,capture_output=True,timeout=180)
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(name+'.'+k)).write_bytes(v)
 return a
for name in ['fixed_math_destinations','fixed_math_lifetimes','fixed_math_capacity']:
 for opt in [0,2]:
  stem=name+f'-O{opt}';f=r/'test/codegen'/(name+'.goose');c=p/(stem+'.c')
  a=run(stem+'-emit',[exe,f'-O{opt}','--standalone','-o',c,f]);assert not a.returncode,(stem,a.stderr)
  for backend,flags in [('gcc',[]),('clang-ubsan',['-fsanitize=undefined','-fno-sanitize-recover=all'])]:
   out=p/(stem+'-'+backend+'.native');cc='clang' if flags else 'cc'
   a=run(stem+'-'+backend+'-cc',[cc,f'-O{opt}',*flags,c,'-pthread','-lm','-ldl','-o',out]);assert not a.returncode,a.stderr
   a=run(stem+'-'+backend+'-run',[out]);expected=(r/'test/expected'/(name+'.out')).read_bytes()
   assert a.stdout==expected,(stem,backend,a)
   if name=='fixed_math_capacity':assert a.returncode!=0 and b'limited array capacity exceeded' in a.stderr,(stem,backend,a)
   else:assert a.returncode==0 and not a.stderr,(stem,backend,a)
   rows.append({'case':name,'opt':opt,'backend':backend,'exit':a.returncode,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'c_sha256':hashlib.sha256(c.read_bytes()).hexdigest()})
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS',len(rows),'native regression builds/runs with required output/reason')
