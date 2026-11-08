from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;q=p/'parent03';q.mkdir(exist_ok=True);r=Path('/home/dev/Projects/goose-wasm-backend');exe=Path('/tmp/goose-wasm-array-expression-source-20261108/build01/goose-tested');cases={}
for sk,sp in [('u8','[u8]'),('u16','[u16]'),('u32','[u32]'),('leb','[varint]')]:
 for tk,tp in [('u8','[u8]'),('u16','[u16]'),('u32','[u32]'),('leb','[varint]'),('grow','[>..]'),('runtime','[..]')]:
  if sk==tk:continue
  name=sk+'_to_'+tk;extra='b.push(99);assert(b.len==3&&b[2]==99);' if tk=='grow' else 'assert(b.cap==2);' if tk=='runtime' else ''
  cases[name]=f'fn main(){{var a:i64{sp}=[7,-8];var b:i64{tp}=copy(a);assert(b.len==2&&b[0]==7&&b[1]== -8);b[0]=31;assert(a[0]==7);{extra}print("{name}");}}\n'
for name,sp,tp,n in [('empty','[u8]','[u16]',0),('leb127','[u16]','[varint]',127),('leb128','[u16]','[varint]',128),('leb16384','[u32]','[varint]',16384),('u8_255','[varint]','[u8]',255),('u16_256','[varint]','[u16]',256),('u16_65535','[u32]','[u16]',65535),('u32_65536','[varint]','[u32]',65536)]:
 check=f'assert(b[0]==73&&b[{n-1}]==73);' if n else ''
 cases[name]=f'fn main(){{var a:u8{sp}=[73;{n}];var b:u8{tp}=copy(a);assert(b.len=={n}&&a.len=={n});{check}print("{name}");}}\n'
cases.update({
 'padded':'struct S{a:u8,b:i64,c:u16}fn main(){var a:S[u8]=[S{7,-8,900},S{9,10,800}];var b:S[u16]=copy(a);assert(b.len==2&&b[0].a==7&&b[0].b== -8&&b[0].c==900&&b[1].c==800);b[0].a=99;assert(a[0].a==7);print("padded");}\n',
 'refs':'struct S{n:i64}fn main(){var first=S{7};var second=S{8};var a:S&[u8]=[first,second];var b:S&[varint]=copy(a);assert(b.len==2&&b[0] .== &first&&b[1] .== &second);b[0].n=99;assert(first.n==99);print("refs");}\n',
 'ref_call':'var calls:i64=0;recursive fn choose(a:u8[u8]&)->u8[u8]&{calls++;a[0]=31;return a;}fn main(){var a:u8[u8]=[7,8];var b:u8[u16]=copy(choose(a));assert(calls==1&&b.len==2&&b[0]==31&&b[1]==8);b[0]=99;assert(a[0]==31);print("ref_call");}\n',
 'inline_ref_call':'var calls:i64=0;inline fn choose(a:u8[varint]&)->u8[varint]&{calls++;return a;}fn main(){var a:u8[varint]=[7,8];var b:u8[u16]=copy(choose(a));assert(calls==1&&b.len==2&&b[1]==8);print("inline_ref_call");}\n',
 'dynamic_memory':'recursive fn take(a:u8[u8]&){var b:u8[u16]=copy(a);assert(b.len==2&&b[0]==7&&b[1]==8);b[0]=99;assert(a[0]==7);}fn main(){var a:u8[u8]=[7,8];var c:u8[u8]=[7,8];take(a);take(c);print("dynamic_memory");}\n',
 'reference_index':'fn main(){var a:u8[u8]=[7,8];var refs:u8[u8]&[1]=[a];var b:u8[u16]=copy(refs[0]);assert(b.len==2&&b[1]==8);print("reference_index");}\n',
 'global':'var a:u8[u8]=[7,8];var b:u8[u16]=copy(a);fn main(){assert(b.len==2&&b[1]==8);b[0]=99;assert(a[0]==7);print("global");}\n',
 'loop_cleanup':'fn main(){var visits:i64=0;for i in 3{var a:u8[u8]=[7,8];var b:u8[varint]=copy(a);assert(b.len==2&&b[1]==8);if i==0{continue;}visits++;if i==1{break;}}assert(visits==1);print("loop_cleanup");}\n',
})
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
