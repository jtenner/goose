from pathlib import Path
import json,hashlib
p=Path(__file__).parent;d=p/'image-sources';d.mkdir(exist_ok=True);rows=[]
for count in [0,127,128,16383,16384]:
 name=f'image_fill{count}';s=f'struct S{{mark:u8,n:i64,tail:u16}}recursive fn value()->i64{{print("eval");return -8;}}fn main(){{print("before");var a:S[varint]=[S{{34,value(),900}};{count}];print("after");assert(a.len=={count});'+(f'assert(a[{count-1}].n== -8&&a[0].tail==900);' if count else '')+'}\n';(d/(name+'.goose')).write_text(s);rows.append({'case':name,'source_sha256':hashlib.sha256(s.encode()).hexdigest(),'expected':'before\neval\nafter\n','persistent':0})
for count in [0,128]:
 name=f'image_copy{count}';s=f'struct S{{mark:u8,n:i64,tail:u16}}recursive fn receive(a:S[varint]&){{print("before");var b:S[varint]=copy(a);print("after");assert(b.len=={count});'+(f'assert(b[{count-1}].n== -8&&b[0].tail==900);' if count else '')+f'}}fn main(){{var a:S[varint]=[S{{34,-8,900}};{count}];receive(a);print("between");var keep:u8[]=[91];receive(a);print("done");assert(keep[0]==91);}}\n';(d/(name+'.goose')).write_text(s);rows.append({'case':name,'source_sha256':hashlib.sha256(s.encode()).hexdigest(),'expected':'before\nafter\nbetween\nbefore\nafter\ndone\n','persistent':0})
(p/'image-families.json').write_text(json.dumps(rows,indent=2)+'\n');print('Prepared',len(rows),'unexecuted image families')
