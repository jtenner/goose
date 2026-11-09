from pathlib import Path
import json,hashlib,shutil
p=Path(__file__).parent;d=p/'prepared';d.mkdir(exist_ok=True);r=Path('/home/dev/Projects/goose-wasm-backend');rows=[]
def add(name,text,expected=None,persistent=0):
 if expected is None:expected=name+'\n'
 if not text.endswith('\n'):text+='\n'
 (d/(name+'.goose')).write_text(text);rows.append({'case':name,'source_sha256':hashlib.sha256(text.encode()).hexdigest(),'expected':expected,'persistent':persistent})
for old in ['struct_fill','empty_effect','nested_fill','enum_fill','reference','data_reference','default_value','zero_exit','loop_exits','standalone_variant']:
 f=r/'test/wasm'/('wasm_aggregate_data_fill_'+old+'.goose');s=f.read_text()
 for width in [8,16,32,64]:s=s.replace(f'[u{width}]','[varint]')
 name='fill_'+old;add(name,s,expected=(r/'test/expected'/('wasm_aggregate_data_fill_'+old+'.out')).read_text())
for n in [127,128,16383,16384]:
 name=f'fill_count{n}';add(name,f'struct S{{mark:u8,n:i64,tail:u16}}fn main(){{var a:S[varint]=[S{{7,-8,900}};{n}];assert(a.len=={n}&&a[{n-1}].n== -8&&a[{n-1}].tail==900);print("{name}");}}')
add('literal_empty','struct S{n:i64}fn main(){var a:S[varint]=[];assert(a.len==0);print("literal_empty");}')
add('literal128','struct S{n:i64}fn main(){var a:S[varint]=['+','.join('S{'+str(n)+'}' for n in range(128))+'];assert(a.len==128&&a[0].n==0&&a[127].n==127);print("literal128");}')
add('copy128','struct S{mark:u8,n:i64,tail:u16}fn main(){var a:S[varint]=[S{7,-8,900};128];var b:S[varint]=copy(a);assert(b.len==128&&b[127].n== -8);b[0].n=99;assert(a[0].n== -8&&b[1].n== -8);print("copy128");}')
add('convert','struct S{n:i64}fn main(){var a:S[u16]=[S{7};128];var b:S[varint]=copy(a);var c:S[u8]=copy(b);assert(b.len==128&&c[127].n==7);b[0].n=99;assert(a[0].n==7&&c[0].n==7);print("convert");}')
add('fixed_source','struct S{n:i64}fn main(){var a:S[2]=[S{7},S{9}];var b:S[varint]=copy(a);assert(b.len==2&&b[1].n==9);print("fixed_source");}')
add('limited_source','struct S{n:i64}fn main(){var a:S[..4]=[S{7},S{9}];var b:S[varint]=copy(a);assert(b.len==2&&b[1].n==9);print("limited_source");}')
add('borrow','struct S{n:i64}recursive fn check(a:S[varint]&)->i64{var b:S[varint]=copy(a);assert(b[127].n==7);return b.len;}fn main(){var a:S[varint]=[S{7};128];assert(check(a)==128);var keep:u8[]=[91];assert(check(a)==128&&keep[0]==91);print("borrow");}')
add('reference_field','struct S{n:i64}struct H{a:S[varint]&}fn main(){var a:S[varint]=[S{7};128];var holders:H[]=[H{a}];var b:S[varint]=copy(holders[0].a);assert(b.len==128&&b[127].n==7);print("reference_field");}')
add('global','struct S{n:i64}var a:S[varint]=[S{7};128];fn main(){var b:S[varint]=copy(a);assert(b.len==128&&b[127].n==7);print("global");}',persistent=1)
# The established copied iteration spelling is taken from its regression corpus.
add('iteration','struct S{n:i64}fn main(){var a:S[varint]=[S{7};128];var sum:i64=0;for copy row in a{sum+=row.n;}assert(sum==896);print("iteration");}')
(p/'prepared-families.json').write_text(json.dumps(rows,indent=2)+'\n');print('Prepared',len(rows),'unexecuted LEB aggregate families')
shutil.copy2('/tmp/goose-wasm-aggregate-data-fill-20261109/run_suite.py',p/'run_suite.py');(p/'parent-compiler-identity.json').write_text(json.dumps({'parent':'c727452fdf7c585e277b8bb3e19f2a91d4a19836','compiler':'/tmp/goose-wasm-aggregate-data-fill-20261109/build01/goose-tested','sha256':'8a807ab28e4e837c84d99199b015fb3159bd26432c5d43c3d8188f88f3a71f3f'},indent=2)+'\n')
