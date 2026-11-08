from pathlib import Path
import subprocess,json,hashlib,shutil
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;old=Path('/tmp/goose-wasm-limited-source-next-20261108/parent01');dest=p/'parent01';dest.mkdir(exist_ok=True)
source_hashes=json.loads(Path('/tmp/goose-wasm-limited-array-layout-20261108/build02/source-hashes.json').read_text())
for n,h in source_hashes.items():assert hashlib.sha256(subprocess.check_output(['git','show','ca0a5a7b5c0f105d742fa1cdc9e16c488a7b4da3:'+n],cwd=r)).hexdigest()==h,n
rows=json.loads((old/'results.json').read_text());assert len(rows)==46
for row in rows:
 name=row['case'];f=old/(name+'.goose');assert hashlib.sha256(f.read_bytes()).hexdigest()==row['source_sha256'];assert row['native_exit']==0 and row['wasm_exit']==1
 for s in old.glob(name+'*'):
  if s.suffix in ['.goose','.json','.stdout','.stderr','.exit']:shutil.copy2(s,dest/s.name)
 (r/'test/wasm'/('wasm_limited_array_conversion_'+name+'.goose')).write_bytes(f.read_bytes());(r/'test/expected'/('wasm_limited_array_conversion_'+name+'.out')).write_bytes((old/(name+'-native.stdout')).read_bytes())
(dest/'results.json').write_bytes((old/'results.json').read_bytes());(dest/'compiler-identity.json').write_bytes((old/'compiler-identity.json').read_bytes())
(p/'parent-reuse.json').write_text(json.dumps({'status':'PASS','parent_commit':'ca0a5a7b5c0f105d742fa1cdc9e16c488a7b4da3','source_hashes_match_commit':len(source_hashes),'producer_directory':str(old),'copied_record_directory':str(dest),'preserve_original_command_paths':True,'reused_families':46},indent=2)+'\n')
q=p/'parent02';q.mkdir(exist_ok=True);exe=Path('/tmp/goose-wasm-limited-array-layout-20261108/build02/goose-tested')
cases={
 'runtime_256':(p/'runtime-width01/case.goose').read_text(),
 'runtime_65536':'fn main(){var a:u8[..65536]=[];for i in 0..65536{a.push(i as u8);}var b:u8[..]=a;assert(b.len==65536&&b.cap==65536&&b[65535]==255);print("runtime65536");}\n',
 'u8_255':'fn main(){var a:u8[..256]=[];for i in 0..255{a.push(i as u8);}var b:u8[u8]=a;assert(b.len==255&&b[254]==254);print("u8_255");}\n',
 'zero_call_variable':'recursive fn make()->u8[..0]{print("inside");return[];}fn main(){var b:u8[]=make();assert(b.len==0);print("zero_call_variable");}\n',
 'zero_call_runtime':'recursive fn make()->u8[..0]{print("inside");return[];}fn main(){var b:u8[..]=make();assert(b.len==0&&b.cap==0);print("zero_call_runtime");}\n',
 'early_return':'recursive fn use(a:u8[..3]&)->i64{var b:u8[]=a;return b[1];}fn main(){var a:u8[..3]=[7,8];assert(use(a)==8);var sibling:u8[]=[99];assert(use(a)==8&&sibling[0]==99);print("early_return");}\n',
 'owner_varint':'fn main(){var a:u8[..256]=[];for i in 0..128{a.push(i as u8);}print("before");var b:u8[varint]=a;print("after");assert(b.len==128&&b[127]==127);}\n',
 'large_capacity_small':'fn main(){var a:u8[..65536]=[7,8];var b:u8[u8]=a;assert(b.len==2&&b[1]==8);print("large_capacity_small");}\n',
}
rows=[]
for name,source in cases.items():
 f=q/(name+'.goose');f.write_text(source);row={'case':name,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
 for kind,args in [('emit',[exe,'--standalone','-o',q/(name+'.c'),f]),('cc',['cc',q/(name+'.c'),'-pthread','-lm','-ldl','-o',q/(name+'.native')]),('native',[q/(name+'.native')]),('wasm',[exe,'--target','wasm','-o',q/(name+'.wasm'),f])]:
  args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120);row[kind+'_exit']=a.returncode
  for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (q/(name+'-'+kind+'.'+k)).write_bytes(v)
  (q/(name+'-'+kind+'.json')).write_text(json.dumps(args)+'\n')
  if a.returncode and kind!='wasm':break
 if row.get('native_exit')==0:
  (r/'test/wasm'/('wasm_limited_array_conversion_'+name+'.goose')).write_bytes(f.read_bytes());(r/'test/expected'/('wasm_limited_array_conversion_'+name+'.out')).write_bytes((q/(name+'-native.stdout')).read_bytes())
 rows.append(row)
(q/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('extra native-valid',sum(x.get('native_exit')==0 for x in rows),'of',len(rows));print([x for x in rows if x.get('native_exit')!=0])
