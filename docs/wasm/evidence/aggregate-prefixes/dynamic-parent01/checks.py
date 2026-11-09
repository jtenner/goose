from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');exe=Path('/tmp/goose-wasm-array-prefix-conversion-20261108/build01/goose-tested')
f=p/'dynamic.goose';f.write_text('struct S{mark:u8,cells:u16[2],limited:u16[..3],tail:u8}recursive fn produce(seed:i64)->i64{print("before");var rows:S[]=[S{1,[11,22],[33,44],2},S{3,[55,66],[],4}];print("after");assert(rows[0].limited[1]==44&&rows[1].tail==4);return seed+7;}fn main(){assert(produce(0)==7);var keep:u8[]=[91];assert(produce(1)==8&&keep[0]==91);print("done");}\n')
i=0;row={'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
for phase,args in [('emit',[exe,'--standalone','-o',p/'dynamic.c',f]),('cc',['cc',p/'dynamic.c','-pthread','-lm','-ldl','-o',p/'dynamic.native']),('native',[p/'dynamic.native']),('wasm',[exe,'-O0','--target','wasm','-o',p/'dynamic.wasm',f]),('validate',['wasm-tools','validate',p/'dynamic.wasm']),('node',['node',r/'scripts/run_wasm.mjs',p/'dynamic.wasm'])]:
 args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120);row[phase+'_exit']=a.returncode
 (p/(phase+'.json')).write_text(json.dumps(args)+'\n')
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(phase+'.'+k)).write_bytes(v)
 assert not a.returncode,(phase,a.stderr)
 if phase in ['native','node']:assert a.stdout==b'before\nafter\nbefore\nafter\ndone\n'
(p/'results.json').write_text(json.dumps(row,indent=2)+'\n');print('PASS native and accepted-parent active-value checks; dirty-image probe follows')
