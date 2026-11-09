from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;q=p/'parent02';q.mkdir(exist_ok=True);r=Path('/home/dev/Projects/goose-wasm-backend');exe=Path('/tmp/goose-wasm-array-prefix-conversion-20261108/build01/goose-tested');cases={}
for prefix in ['u8','u16','u64']:
 t=f'S[{prefix}]';decl='struct S{n:i64}'
 cases[prefix+'_byref']=decl+f'fn main(){{var a:{t}=[S{{7}},S{{8}}];for &s in a{{s.n+=10;}}assert(a[0].n==17&&a[1].n==18);print("{prefix}_byref");}}\n'
 cases[prefix+'_ref_field']=decl+f'struct H{{before:u8,rows:{t}&,after:u16}}fn main(){{var a:{t}=[S{{7}},S{{8}}];var holders:H[]=[H{{77,a,900}}];var b:{t}=copy(holders[0].rows);b[0].n=99;assert(a[0].n==7&&b[0].n==99&&holders[0].before==77&&holders[0].after==900);var total:i64=0;for s in holders[0].rows{{total+=s.n;}}assert(total==15);print("{prefix}_ref_field");}}\n'
 cases[prefix+'_recursion']=decl+f'var calls:i64=0;recursive fn walk(views:{t}&[3]&,depth:i64,parent:S?)->i64{{calls++;var saved:i64[2]=[depth,90+depth];var total:i64=0;for s in views[depth]{{if parent{{assert(&s .!= parent&&parent.n==s.n+1);}}assert(s.n==depth+1);if depth>0{{total+=walk(views,depth-1,s);}}assert(s.n==depth+1&&saved[0]==depth&&saved[1]==90+depth);total+=s.n;}}return total;}}fn main(){{var a:{t}=[S{{1}}];var b:{t}=[S{{2}}];var c:{t}=[S{{3}}];var views:{t}&[3]=[a,b,c];assert(walk(views,2,null)==6&&calls==3);print("{prefix}_recursion");}}\n'
 cases[prefix+'_bits']='struct S{flag:bool,small:f32,wide:f64,special:f64,bits:bool[2]}'+f'fn main(){{var a:{t}=[S{{true,-0.0,-2.5,0.0/0.0,[true,false]}},S{{false,1.25,3.5,0.0/0.0,[false,true]}}];var b:{t}=copy(a);assert(b[0].flag&&!b[1].flag&&b[0].wide== -2.5&&b[1].small==1.25&&b[0].special!=b[0].special&&1.0/b[0].small<0.0&&b[1].bits[1]);b[0].wide=99.0;assert(a[0].wide== -2.5);print("{prefix}_bits");}}\n'
 cases[prefix+'_cleanup']=decl+f'recursive fn probe(yes:bool)->i64{{var a:{t}=[S{{7}},S{{8}}];var total:i64=0;for s in a{{var copy:{t}=copy(a);assert(copy[1].n==8);if yes{{return s.n;}}defer total+=s.n;}}return total;}}fn main(){{assert(probe(true)==7&&probe(false)==15);print("{prefix}_cleanup");}}\n'
cases['padded_cross']='struct S{a:u8,b:i64,c:u16}fn main(){var a:S[u8]=[S{7,-8,900},S{9,10,800}];var b:S[u16]=copy(a);assert(b.len==2&&b[0].a==7&&b[0].b== -8&&b[0].c==900&&b[1].c==800);b[0].a=99;assert(a[0].a==7);print("padded_cross");}\n'
cases['u64_to_u8']='struct S{a:u8,b:i64,c:u16}fn main(){var a:S[u64]=[S{7,-8,900},S{9,10,800}];var b:S[u8]=copy(a);assert(b.len==2&&b[0].b== -8&&b[1].c==800);b[0].a=99;assert(a[0].a==7);print("u64_to_u8");}\n'
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
