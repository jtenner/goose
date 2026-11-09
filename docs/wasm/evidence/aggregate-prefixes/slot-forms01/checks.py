from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');parent=Path('/tmp/goose-wasm-array-prefix-conversion-20261108/build01/goose-tested');prototype=p.parent/'build01/goose-tested';rows=[]
cases={}
for name,partial in [('numeric','[4]'),('empty','[]'),('fill','[4;1]'),('default','default<u16[..3]>()')]:cases[name]=('', 'u16','[1,2,3]',partial,'r==0','r','')
cases['fill_zero']=('var calls:i64=0;recursive fn value()->u16{calls++;return 4;}','u16','[1,2,3]','[value();0]','r==0&&calls==1','r',',",calls=",calls')
for name,partial in [('text','"a"'),('text_empty','""')]:cases[name]=('','u8','[1,2,3]',partial,'r==0','r','')
for name,partial in [('nominal','[Cell{4}]'),('nominal_empty','[]'),('nominal_fill','[Cell{4};1]'),('nominal_default','default<Cell[..3]>()')]:cases[name]=('struct Cell{n:u16}','Cell','[Cell{1},Cell{2},Cell{3}]',partial,'r.n==0','r.n','')
cases['nominal_fill_zero']=('struct Cell{n:u16}var calls:i64=0;recursive fn value()->Cell{calls++;return Cell{4};}','Cell','[Cell{1},Cell{2},Cell{3}]','[value();0]','r.n==0&&calls==1','r.n',',",calls=",calls')
for kind in ['f32','f64']:cases[kind]=('',kind,'[1.0,2.0,3.0]','[4.0]','r==0.0','r','')
cases['bool']=('','bool','[true,true,true]','[false]','!r','r','')
for name,(decl,elem,full,partial,check,show,extra) in cases.items():
 f=p/(name+'.goose');f.write_text(decl+f'struct S{{xs:{elem}[..3]}}fn main(){{var a:S[]=[S{{{full}}}];var r:{elem}& =a[0].xs[2];for i in 2{{if i==0{{a[0]=S{{{full}}};}}else{{a[0]=S{{{partial}}};}}}}print("slot=",{show}{extra});assert({check});}}\n');row={'case':name,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
 for label,exe in [('native',parent),('parent',parent),('prototype',prototype)]:
  stem=p/(name+'-'+label);c,native,module=(stem.with_suffix(ext) for ext in ['.c','.native','.wasm']);commands=[('emit',[exe,'--standalone','-o',c,f]),('cc',['cc',c,'-pthread','-lm','-ldl','-o',native]),('run',[native])] if label=='native' else [('emit',[exe,'-O0','--target','wasm','-o',module,f]),('validate',['wasm-tools','validate',module]),('run',['node',r/'scripts/run_wasm.mjs',module])]
  for phase,args in commands:
   args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120);row[label+'_'+phase+'_exit']=a.returncode
   stem2=p/(name+'-'+label+'-'+phase);stem2.with_suffix('.json').write_text(json.dumps(args)+'\n')
   for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: Path(str(stem2)+'.'+k).write_bytes(v)
   if phase=='run':row[label+'_stdout']=a.stdout.decode();row[label+'_stderr']=a.stderr.decode()
   if a.returncode:break
 rows.append(row)
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
