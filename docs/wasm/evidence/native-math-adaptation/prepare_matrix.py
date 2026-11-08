from pathlib import Path
import json
p=Path(__file__).parent
cases={}
for op,expr,values in [('neg','-a',[-7,8]),('add','a+a',[14,-16]),('sub','a-a',[0,0]),('mul','a*a',[49,64]),('div','a/a',[1,1]),('mod','a%a',[0,0]),('left','2*a',[14,-16]),('right','a*2',[14,-16])]:
 for storage in ['i64[..2]','i64[..3]','i64[]','i64[>..]']:
  name=op+'_'+str(['i64[..2]','i64[..3]','i64[]','i64[>..]'].index(storage))
  cases[name]=f'fn main(){{var a:i64[2]=[7,-8];var b:{storage}={expr};assert(b.len==2);assert(b[0]=={values[0]});assert(b[1]=={values[1]});assert(a[0]==7);assert(a[1] == -8);print("{name}");}}\n'
for op,expr,x,y in [('neg','-a',-7,8),('add','a+a',14,-16)]:
 for context in ['assign','return','argument','nested','array']:
  name=op+'_'+context
  check=f'assert(b.len==2);assert(b[0]=={x});assert(b[1]=={y});'
  if context=='assign':pre='';body=f'var b:i64[..3]=[1,2,3];b={expr};'+check
  if context=='return':pre=f'fn result(a:i64[2])->i64[..3]{{return {expr};}}';body='let b=result(a);'+check
  if context=='argument':pre=f'fn consume(b:i64[..3]){{{check}}}';body=f'consume({expr});'
  if context=='nested':pre='struct Box{b:i64[..3]}';body=f'let box=Box{{b:{expr}}};let b=box.b;'+check
  if context=='array':pre='';body=f'let boxes:i64[..3][1]=[{expr}];let b=boxes[0];'+check
  cases[name]=pre+f'fn main(){{var a:i64[2]=[7,-8];{body}print("{name}");}}\n'
cases['alias']='fn main(){var a:i64[2]=[7,-8];a=-a;assert(a[0] == -7);assert(a[1]==8);a=a*a;assert(a[0]==49);assert(a[1]==64);print("alias");}\n'
cases['float']='fn main(){var a:f64[2]=[1.25,-2.5];var b:f64[..4]=-a;assert(b.len==2);assert(b[0] == -1.25);assert(b[1]==2.5);var c:f64[..4]=a+a;assert(c.len==2);assert(c[0]==2.5);assert(c[1] == -5.0);print("float");}\n'
(p/'matrix-cases.json').write_text(json.dumps(cases,indent=2)+'\n')
print(len(cases),'cases prepared')
