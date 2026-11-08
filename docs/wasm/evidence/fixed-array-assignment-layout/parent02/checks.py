from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');exe=Path('/tmp/goose-wasm-fixed-result-layout-20261108/build01/goose-tested');rows=[]
def run(stem,args):
 a=subprocess.run(list(map(str,args)),cwd=r,capture_output=True,timeout=120)
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(stem+'.'+k)).write_bytes(v)
 (p/(stem+'.json')).write_text(json.dumps(list(map(str,args)))+'\n')
 return a
for n in json.loads((p.parent/'cases-more.json').read_text()):
 f=p/(n+'.goose');c=p/(n+'.c');native=p/(n+'.native');module=p/(n+'.wasm');row={'case':n,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
 a=run(n+'-emit',[exe,'-O0','--standalone','-o',c,f]);row['native_emit_exit']=a.returncode
 if a.returncode:row['native_reason']=a.stderr.decode();rows.append(row);continue
 a=run(n+'-cc',['cc',c,'-pthread','-lm','-ldl','-o',native]);assert not a.returncode,a.stderr
 a=run(n+'-native',[native]);assert not a.returncode and a.stdout==json.loads((p.parent/'expected-more.json').read_text())[n].encode(),(n,a)
 a=run(n+'-wasm',[exe,'-O0','--target','wasm','-o',module,f]);assert a.returncode in (0,1),(n,a)
 if not a.returncode:
  row.update(native='PASS',wasm='already-supported');rows.append(row);continue
 assert not module.exists(),(n,a)
 row.update(native='PASS',wasm_reason=a.stderr.decode());rows.append(row)
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('recorded',len(rows),'cases;',sum(x.get('native')=='PASS' for x in rows),'native-valid Wasm failures')
