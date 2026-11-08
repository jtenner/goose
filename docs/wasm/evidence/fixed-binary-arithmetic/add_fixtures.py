from pathlib import Path
import json
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');cases=json.loads((p/'cases.json').read_text());more=json.loads((p/'cases-more.json').read_text());more['projection']=json.loads((p/'cases-corrected.json').read_text())['projection'];cases.update(more)
base='struct S{a:f32,pad 2,b:f64}\nvar left:S=S{1.25,45.125};var right:S=S{-2.5,-37.25};\nrecursive fn prepare(l:S&,r:S&){l.a=1.25;l.b=45.125;r.a = -2.5;r.b = -37.25;print("before");}\n'
cases['owner']=base+'fn main(){prepare(left,right);var result:S=left+right;print("after=",result.a==result.a,",",result.b==result.b);}'
cases['data_owner']=base+'fn main(){prepare(left,right);var rows:S[]=[left+right];print("after=",rows[0].a==rows[0].a,",",rows[0].b==rows[0].b);}'
cases['snapshot_owner']='var source:i64[2]=[7,-8];var calls:i64=0;recursive fn source_value()->i64[2]&{calls++;return source;}recursive fn change()->i64[2]{source[0]=99;print("right");return [3,4];}fn main(){print("before");var result:i64[2]=source_value()+change();print("after=",result[0],",",result[1],",",calls);}'
for n,s in cases.items():
 name='wasm_fixed_binary_'+n
 (r/'test/wasm'/(name+'.goose')).write_text(s+'\n')
 expected=('before\nafter=true,true\n' if n in ['owner','data_owner'] else 'before\nright\nafter=10,-4,1\n' if n=='snapshot_owner' else 'head\n'*4+'early_continue\n' if n=='early_continue' else n+'\n')
 (r/'test/expected'/(name+'.out')).write_text(expected)
(p/'positive-cases.json').write_text(json.dumps(cases,indent=2)+'\n');print(len(cases),'positive families')
p=r/'test/wasm_backend.py';s=p.read_text();s=s.replace("'wasm_fixed_negation_')):","'wasm_fixed_negation_', 'wasm_fixed_binary_')):")
needle="            if source.stem.startswith('wasm_fixed_negation_'):\n"
assert s.count(needle)==1
s=s.replace(needle,"""            if source.stem.startswith('wasm_fixed_binary_'):
                mode = '' if source.stem in ('wasm_fixed_binary_data', 'wasm_fixed_binary_index_effect',
                                            'wasm_fixed_binary_data_owner') else 'no-data'
                checked = run([args.node, ROOT / 'test/wasm_multimemory.mjs', wasm, '0', mode])
                assert checked.stdout == reference.stdout and not checked.stderr
                count += 1
"""+needle)
p.write_text(s)
