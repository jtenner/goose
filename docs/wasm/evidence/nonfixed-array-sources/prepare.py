from pathlib import Path
import json,hashlib
p=Path(__file__).parent;q=p/'prepared';q.mkdir(exist_ok=True);cases={}
def add(name,body,head=''):
 cases[name]=head+'fn main(){'+body+'print("'+name+'");}\n'
for source,layout in [('grow','[>..]'),('runtime','[..]')]:
 for target,dest in [('u8','[u8]'),('u16','[u16]'),('u64','[u64]'),('leb','[varint]'),('runtime' if source=='grow' else 'grow','[..]' if source=='grow' else '[>..]')]:
  name=source+'_to_'+target
  tail='assert(b.cap==2);' if target=='runtime' else 'b.push(99);assert(b.len==3&&b[2]==99);' if target=='grow' else ''
  add(name,f'var a:i64{layout}=[7,-8];var b:i64{dest}=copy(a);assert(b.len==2&&b[0]==7&&b[1]== -8);b[0]=31;assert(a[0]==7);'+tail)
  add(source+'_empty_to_'+target,f'var a:i64{layout}=[];var b:i64{dest}=copy(a);assert(a.len==0&&b.len==0);'+('assert(b.cap==0);' if target=='runtime' else ''))
 add(source+'_reference',f'var a:i64{layout}=[7,-8];var r:i64{layout}& =a;var b:i64[u16]=copy(r);assert(b.len==2&&b[0]==7&&b[1]== -8);b[0]=91;assert(a[0]==7);')
 add(source+'_indexed_reference',f'var a:i64{layout}=[7,-8];var c:i64{layout}=[9];var refs:i64{layout}&[2]=[a,c];var b:i64[u16]=copy(refs[0]);assert(b.len==2&&b[0]==7&&b[1]== -8);refs[0].=c;assert(b[0]==7);')
 add(source+'_call_effect',f'var a:i64{layout}=[7,-8];var b:i64[u16]=copy(select(a));assert(calls==1&&a.len==3&&b.len==3&&b[2]==99);',f'var calls=0;recursive fn select(a:i64{layout}&)->i64{layout}&{{calls++;a.push(99);var scratch:u8[]=[1,2,3];assert(scratch[2]==3);return a;}}')
 add(source+'_recursion',f'var a:i64{layout}=[7,-8];assert(convert(a,2)== -9);',f'recursive fn convert(a:i64{layout}&,depth:i64)->i64{{var b:i64[u16]=copy(a);assert(b.len==2&&b[0]==7&&b[1]== -8);if depth==0{{return b[0];}}let n=convert(a,depth-1);assert(b[1]== -8);return n+b[1];}}')
 add(source+'_pop',f'var a:i64{layout}=[7,-8,99];assert(a.pop()==99);var b:i64[u16]=copy(a);assert(a.len==2&&b.len==2&&b[0]==7&&b[1]== -8);')
 add(source+'_refs',f'var n:i64=7;var a:i64&{layout}=[n,n];var b:i64&[u16]=copy(a);assert(b.len==2&&b[0]==7);b[1]=31;assert(n==31&&a[0]==31);')
 add(source+'_loop',f'var a:i64{layout}=[7,-8];var sum:i64=0;for i in 20{{var b:i64[u16]=copy(a);sum+=b[0];if i==0{{continue;}}if i==19{{break;}}}}assert(sum==140&&a[1]== -8);')
 add(source+'_global',f'assert(a.len==2&&b.len==2&&b[0]==7&&b[1]== -8);b[0]=31;assert(a[0]==7);',f'var a:i64{layout}=[7,-8];var b:i64[u16]=copy(a);')
 for ty,value,check in [('u8','255','255'),('i16','-32768','-32768'),('u32','4294967295','4294967295'),('u64','18446744073709551615','18446744073709551615'),('f32','-0.0','-0.0'),('f64','1.25','1.25'),('bool','true','true')]:
  add(source+'_'+ty,f'var a:{ty}{layout}=[{value}];var b:{ty}[u16]=copy(a);assert(b.len==1&&b[0]=={check}&&a[0]=={check});')
add('runtime_spare','var a:i64[..]=[..9];a.push(7);a.push(-8);var b:i64[>..]=copy(a);var c:i64[u8]=copy(a);assert(a.cap==9&&a.len==2&&b.len==2&&c.len==2&&b[1]== -8&&c[0]==7);')
add('runtime_empty_spare','var a:i64[..]=[..9];var b:i64[>..]=copy(a);var c:i64[u8]=copy(a);assert(a.cap==9&&a.len==0&&b.len==0&&c.len==0);')
cases['runtime_call_effect']=cases['runtime_call_effect'].replace('var a:i64[..]=[7,-8];','var a:i64[..]=[..3];a.push(7);a.push(-8);')
for source in ['grow','runtime']:
 cases[source+'_recursion']=(p/'recursion-templates'/(source+'.goose')).read_text()
for name,text in cases.items():(q/(name+'.goose')).write_text(text)
(p/'prepared-families.json').write_text(json.dumps([{'case':n,'source_sha256':hashlib.sha256(t.encode()).hexdigest(),'expected':n+'\n','status':'unrun sketch'} for n,t in cases.items()],indent=2)+'\n')
print('Prepared',len(cases),'unrun correctness sketches outside the repository')
