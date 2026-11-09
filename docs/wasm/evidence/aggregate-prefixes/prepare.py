from pathlib import Path
import json,subprocess,hashlib,shutil
p=Path(__file__).parent;q=p/'parent01';q.mkdir(exist_ok=True);r=Path('/home/dev/Projects/goose-wasm-backend');exe=Path('/tmp/goose-wasm-array-prefix-conversion-20261108/build01/goose-tested');cases={}
for prefix in ['u8','u16','u64']:
 t=f'S[{prefix}]';tag=prefix+'_';decl='struct S{mark:u8,n:i64,tail:u16}'
 cases[tag+'literal']=decl+f'fn main(){{var a:{t}=[S{{7,-8,900}},S{{9,10,800}}];assert(a.len==2&&a[0].n== -8&&a[1].tail==800);print("{tag}literal");}}\n'
 cases[tag+'empty']=decl+f'fn main(){{var a:{t}=[];var b:{t}=copy(a);assert(a.len==0&&b.len==0&&a .!= b);print("{tag}empty");}}\n'
 cases[tag+'copy']=decl+f'fn main(){{var a:{t}=[S{{7,-8,900}},S{{9,10,800}}];var b:{t}=copy(a);b[0].n=31;assert(a.len==2&&b.len==2&&a[0].n== -8&&b[0].n==31&&b[1].tail==800);print("{tag}copy");}}\n'
 cases[tag+'fixed_source']=decl+f'fn main(){{var a:S[2]=[S{{7,-8,900}},S{{9,10,800}}];var b:{t}=a;assert(b.len==2&&b[0].n== -8&&b[1].tail==800);b[0].n=31;assert(a[0].n== -8);print("{tag}fixed_source");}}\n'
 cases[tag+'limited_source']=decl+f'fn main(){{var a:S[..3]=[S{{7,-8,900}},S{{9,10,800}}];var b:{t}=a;assert(b.len==2&&b[0].n== -8&&b[1].tail==800);print("{tag}limited_source");}}\n'
 cases[tag+'prefix_source']=decl+f'fn main(){{var a:S[]=[S{{7,-8,900}},S{{9,10,800}}];var b:{t}=copy(a);assert(b.len==2&&b[0].n== -8&&b[1].tail==800);b[0].n=31;assert(a[0].n== -8);print("{tag}prefix_source");}}\n'
 cases[tag+'iteration']=decl+f'fn main(){{var a:{t}=[S{{7,10,900}},S{{9,20,800}}];var total:i64=0;for s,i in a{{assert(&s .!= &a[i]);a[i].n+=100;assert(s.n==(i+1)*10);total+=s.n;}}assert(total==30&&a[0].n==110&&a[1].n==120);print("{tag}iteration");}}\n'
 cases[tag+'nested']='struct S{before:u8,cells:u16[2],limited:i64[..3],after:u16}'+f'fn main(){{var a:{t}=[S{{7,[100,200],[7,-8],900}},S{{9,[300,400],[],800}}];var b:{t}=copy(a);b[0].cells[1]=31;b[0].limited.push(9);assert(a[0].cells[1]==200&&a[0].limited.len==2&&b[0].cells[1]==31&&b[0].limited.len==3&&b[0].limited[2]==9&&b[1].after==800);print("{tag}nested");}}\n'
 cases[tag+'reference']=decl+f'recursive fn take(a:{t}&)->i64{{return a[0].n+a[1].n;}}fn main(){{var a:{t}=[S{{7,10,900}},S{{9,20,800}}];var b:{t}=[S{{7,30,900}},S{{9,40,800}}];assert(take(a)==30&&take(b)==70);print("{tag}reference");}}\n'
 cases[tag+'global']=decl+f'var a:{t}=[S{{7,-8,900}}];fn main(){{assert(a.len==1&&a[0].n== -8&&a[0].tail==900);print("{tag}global");}}\n'
 cases[tag+'enum']='enum E{A{mark:u8,n:i64},B}'+f'fn main(){{var a:E[{prefix}]=[E.A{{7,-8}},E.B];var b:E[{prefix}]=copy(a);match b[0]{{A v=>{{assert(v.mark==7&&v.n== -8);}},B=>assert(false)}}match b[1]{{B=>{{}},A v=>assert(false)}}print("{tag}enum");}}\n'
rows=[]
for name,source in cases.items():
 f=q/(name+'.goose');f.write_text(source);row={'case':name,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
 for kind,args in [('emit',[exe,'--standalone','-o',q/(name+'.c'),f]),('cc',['cc',q/(name+'.c'),'-pthread','-lm','-ldl','-o',q/(name+'.native')]),('native',[q/(name+'.native')]),('wasm',[exe,'-O0','--target','wasm','-o',q/(name+'.wasm'),f])]:
  args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120);row[kind+'_exit']=a.returncode
  (q/(name+'-'+kind+'.json')).write_text(json.dumps(args)+'\n')
  for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (q/(name+'-'+kind+'.'+k)).write_bytes(v)
  if a.returncode and kind!='wasm':break
 rows.append(row)
(q/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
(p/'parent-compiler-identity.json').write_text(json.dumps({'compiler':str(exe),'sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'source_stage':'/tmp/goose-wasm-array-prefix-conversion-20261108'},indent=2)+'\n');shutil.copy2('/tmp/goose-wasm-array-prefix-conversion-20261108/run_suite.py',p/'run_suite.py')
