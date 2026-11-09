from pathlib import Path
import subprocess,json
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');source=p/'slot.goose'
source.write_text('struct S{xs:u16[..3]}fn main(){var a:S[]=[S{[1,2,3]}];var r:u16& =a[0].xs[2];for i in 2{if i==0{a[0]=S{[1,2,3]};}else{a[0]=S{[4]};}}print("slot=",r);assert(r==0);}\n')
i=0;rows=[]
for label,exe in [('parent','/tmp/goose-wasm-array-prefix-conversion-20261108/build01/goose-tested'),('prototype',p.parent/'build01/goose-tested')]:
 for opt in [0,2]:
  stem=p/f'{label}-O{opt}';c,native,module=(stem.with_suffix(ext) for ext in ['.c','.native','.wasm']);row={'compiler':label,'opt':opt}
  for kind,args in [('emit',[exe,f'-O{opt}','--standalone','-o',c,source]),('cc',['cc',c,'-pthread','-lm','-ldl','-o',native]),('native',[native]),('wasm',[exe,f'-O{opt}','--target','wasm','-o',module,source]),('validate',['wasm-tools','validate',module]),('node',['node',r/'scripts/run_wasm.mjs',module])]:
   i+=1;args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120);row[kind+'_exit']=a.returncode
   (p/f'command-{i:03}.json').write_text(json.dumps(args)+'\n')
   for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/f'command-{i:03}.{k}').write_bytes(v)
   if a.returncode and kind not in ['native','node']:break
   if kind in ['native','node']:row[kind+'_stdout']=a.stdout.decode();row[kind+'_stderr']=a.stderr.decode()
  rows.append(row)
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
