"""LEB aggregate owners: complete images, exact copies and retained guards."""
from pathlib import Path
import re,json
from wasm_data_iteration_checks import function_span
from wasm_fixed_binary_checks import emit
ROOT=Path(__file__).resolve().parents[1]


def one(text,pattern,value):
    text,n=re.subn(pattern,value,text,count=1);assert n==1,pattern
    return text


def check_fill_images(run,node,validator,out):
    checks=0
    for opt in (0,2):
        for count in [0,127,128,16383,16384]:
            name=f'wasm_aggregate_leb_image_fill{count}-O{opt}';text=run([validator,'print',out/(name+'.wasm')]).stdout.decode();args=[node,ROOT/'test/wasm_aggregate_leb_fill_image.mjs'];record=out/(name+'.json')
            result=run(args+[emit(run,validator,out,name+'-healthy',text,2),str(count),record]);assert result.stdout==b'before\neval\nafter\n' and not result.stderr;checks+=1
            state=json.loads(record.read_text());a,z=function_span(text,'main');body=text[a:z];value=re.search(r'call \$value\.\d+\b',body);assert value
            controls=[
                ('no-eval',body[:value.start()]+'i64.const -8'+body[value.end():],b'LEB fill initializer checkpoint differs'),
                ('snapshot-cleanup',one(body,r'global.set 0\b','drop'),b'LEB snapshot restore differs'),
                ('receiver-cleanup',one(body,r'global.set 1\b','drop'),b'LEB completed data top differs')]
            # InitArrayCount emits the canonical constant bytes for literals.
            first=(count%128) | (128 if count>=128 else 0)
            controls.append(('prefix',one(body,rf'i64.const {first}\n(\s*)i64.store8 1\b',lambda m:m[0].replace(f'i64.const {first}',f'i64.const {first^1}',1)),b'LEB fill data image differs'))
            if count:
                for label,size in [('short',10),('long',12)]:controls.append((label,one(body,r'i32.const 11(?=\n\s*memory.copy 1 0\b)',f'i32.const {size}'),b'LEB fill data image differs'))
                controls.append(('source-memory',one(body,r'memory.copy 1 0\b','memory.copy 1 1'),b'LEB fill data image differs'))
                copy=re.search(r'memory.copy 1 0\b',body).start();offsets=list(re.finditer(rf'i64.const {state["prefix"]}\n\s*i64.add\n\s*local.set \d+',body[:copy]));assert offsets;part=offsets[-1]
                changed=body[:part.start()]+one(part[0],rf'i64.const {state["prefix"]}\b',f'i64.const {state["prefix"]+1}')+body[part.end():]
                controls.append(('payload-offset',changed,b'LEB fill data image differs'))
                controls.append(('memory0',one(body,r'memory.copy 1 0\b',lambda m:m[0]+f'\n      i32.const {state["initial"]+11}\n      i32.const 0\n      i32.store8'),b'LEB fill memory 0 image differs'))
            for label,changed,reason in controls:
                result=run(args+[emit(run,validator,out,name+'-'+label,text[:a]+changed+text[z:],2),str(count)],ok=False);assert result.returncode==1 and reason in result.stderr,(count,label,result.stderr);checks+=1
    return checks


def check_copy_images(run,node,validator,out):
    checks=0
    for opt in (0,2):
        for count in [0,128]:
            name=f'wasm_aggregate_leb_image_copy{count}-O{opt}';text=run([validator,'print',out/(name+'.wasm')]).stdout.decode();args=[node,ROOT/'test/wasm_aggregate_leb_copy_image.mjs'];record=out/(name+'.json')
            result=run(args+[emit(run,validator,out,name+'-healthy',text,4),str(count),record]);assert result.stdout==b'before\nafter\nbetween\nbefore\nafter\ndone\n' and not result.stderr;checks+=1
            state=json.loads(record.read_text());a,z=function_span(text,'receive');body=text[a:z];copy=r'call \$goose.copy_memory\b'
            controls=[
                ('short',one(body,r'local.get \d+(?=\n\s*call \$goose.copy_memory\b)',f'i32.const {state["bytes"]-1}'),b'LEB copy receiver image differs'),
                ('long',one(body,r'local.get \d+(?=\n\s*call \$goose.copy_memory\b)',f'i32.const {state["bytes"]+1}'),b'LEB copy receiver image differs'),
                ('cleanup',one(body,r'call \$goose.restore_data\b','drop\n      drop'),b'LEB completed receiver top differs'),
                ('memory0',one(body,copy,lambda m:m[0]+f'\n      i32.const {state["initial"]+16}\n      i32.const 0\n      i32.store8'),b'LEB copy memory 0 image differs')]
            source=r'local.get \d+(?=\n\s*local.get \d+\n\s*call \$goose.copy_memory\b)'
            controls.append(('source-memory',one(body,source,lambda m:m[0]+'\n      i64.const 4294967295\n      i64.and\n      i64.const 8589934592\n      i64.or'),b'LEB copy receiver image differs'))
            destination=r'local.get \d+(?=\n\s*local.get \d+\n\s*local.get \d+\n\s*call \$goose.copy_memory\b)'
            controls.append(('destination-memory',one(body,destination,lambda m:m[0]+'\n      i64.const 4294967295\n      i64.and\n      i64.const 8589934592\n      i64.or'),b'LEB copy receiver image differs'))
            if count:
                decoded=re.search(r'call \$goose.read_array_prefix\n\s*local.set (\d+)',body);assert decoded
                changed=body[:decoded.start()]+one(decoded[0],r'local.set \d+\b',f'drop\n      i32.const 1\n      local.set {decoded[1]}')+body[decoded.end():]
                controls.append(('decoded-width',changed,b'LEB copy first receiver top differs'))
            for label,changed,reason in controls:
                result=run(args+[emit(run,validator,out,name+'-'+label,text[:a]+changed+text[z:],4),str(count)],ok=False);assert result.returncode==1 and reason in result.stderr,(count,label,result.stderr);checks+=1
    return checks


def check_guards(run,exe,cc,out):
    checks=0
    source=out/'aggregate-leb-equality.goose';source.write_text('struct S{n:i64}recursive fn same(a:S[varint]&,b:S[varint]&)->bool{return a==b;}fn main(){var a:S[varint]=[S{7}];var b:S[varint]=[S{7}];assert(same(a,b));print("guard");}\n')
    for opt in (0,2):
        prefix=out/f'aggregate-leb-equality-O{opt}';c,native,module=[prefix.with_suffix(e) for e in ['.c','.native','.wasm']]
        run([exe,f'-O{opt}','--standalone','-o',c,source]);run([cc,c,'-pthread','-lm','-ldl','-o',native]);result=run([native]);assert result.stdout==b'guard\n' and not result.stderr
        result=run([exe,f'-O{opt}','--target','wasm','-o',module,source],ok=False);assert result.returncode==1 and b'aggregate array equality needs the pending value lowering' in result.stderr and not module.exists(),result.stderr;checks+=1
    source=out/'aggregate-leb-empty-variant-element.goose';source.write_text('enum E{A,B{n:u8}}fn main(){var a:E.A[varint]=[E.A;2];assert(a.len==2);print("guard");}\n')
    for opt in (0,2):
        for target in ['native','wasm']:
            output=out/f'aggregate-leb-empty-variant-O{opt}.{target}'
            result=run([exe,f'-O{opt}',*(['--standalone'] if target=='native' else ['--target','wasm']),'-o',output,source],ok=False)
            assert result.returncode==1 and b'an element cannot be a variant type with no fields' in result.stderr and not output.exists(),result.stderr;checks+=1
    return checks
