from pathlib import Path
import subprocess,json,hashlib
raw=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');p=raw/'parent04';p.mkdir(exist_ok=True);exe=Path('/tmp/goose-wasm-fixed-array-assignment-layout-20261108/build01/goose-tested');rows=[]
for name in ['wide16','wide32','zero_up','zero_down']:
 text=(raw/'parent03'/(name+'.goose')).read_text();text=text.replace('var a:u8[..256];','var a:u8[..256]=[];').replace('var a:u8[..65536];','var a:u8[..65536]=[];').replace('var a:u8[..0];','var a:u8[..0]=[];')
 f=p/(name+'.goose');f.write_text(text);row={'case':name,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
 for kind,args in [('emit',[exe,'--standalone','-o',p/(name+'.c'),f]),('cc',['cc',p/(name+'.c'),'-pthread','-lm','-ldl','-o',p/(name+'.native')]),('native',[p/(name+'.native')]),('wasm',[exe,'--target','wasm','-o',p/(name+'.wasm'),f])]:
  a=subprocess.run(list(map(str,args)),cwd=r,capture_output=True,timeout=120);row[kind+'_exit']=a.returncode
  for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(name+'-'+kind+'.'+k)).write_bytes(v)
  (p/(name+'-'+kind+'.json')).write_text(json.dumps(list(map(str,args)))+'\n')
  if a.returncode and kind!='wasm':break
 if row.get('native_exit')==0:
  (r/'test/wasm'/('wasm_limited_array_layout_'+name+'.goose')).write_bytes(f.read_bytes());(r/'test/expected'/('wasm_limited_array_layout_'+name+'.out')).write_text(name+'\n')
 rows.append(row)
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows)
