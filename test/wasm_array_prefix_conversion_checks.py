"""Unequal stored prefixes: byte images, range failures and owner cleanup."""
from pathlib import Path
import json,re
from wasm_data_iteration_checks import function_span
from wasm_fixed_binary_checks import emit
ROOT=Path(__file__).resolve().parents[1]


def one(text,pattern,value):
    text,n=re.subn(pattern,value,text,count=1);assert n==1,pattern
    return text


def check_images(run,node,validator,out):
    count=0
    for opt in (0,2):
        for mode,payload in [('width',24),('leb_source',128),('leb_target',128),('empty',0),('overflow',24)]:
            name=f'wasm_array_prefix_conversion_owner_{mode}-O{opt}'
            text=run([validator,'print',out/(name+'.wasm')]).stdout.decode()
            args=[node,ROOT/'test/wasm_array_prefix_conversion_owner.mjs'];record=out/(name+'.json')
            module=emit(run,validator,out,name+'-healthy',text,3)
            result=run(args+[module,mode,record]);assert result.stdout==b'before\nafter\n' and not result.stderr;count+=1
            initial=json.loads(record.read_text())['initial'];a,z=function_span(text,'main');body=text[a:z]
            copy_arg=r'local.get \d+(?=\n\s*memory.copy 2 1\b)'
            controls=[
                ('long',one(body,copy_arg,f'i32.const {payload+1}'),b'prefix conversion receiver image differs'),
                ('memory0',one(body,r'memory.copy 2 1\b',f'memory.copy 2 1\n      i32.const {initial+16}\n      i32.const 0\n      i32.store8'),b'prefix conversion memory 0 image differs'),
                ('source-cleanup',one(body,r'global.set 1\b','drop'),b'prefix conversion completed source top differs'),
                ('receiver-cleanup',one(body,r'global.set 2\b','drop'),b'prefix conversion completed receiver top differs'),
            ]
            if payload:
                controls += [('short',one(body,copy_arg,f'i32.const {payload-1}'),b'prefix conversion receiver image differs'),
                             ('source-memory',one(body,r'memory.copy 2 1\b','memory.copy 2 0'),b'prefix conversion receiver image differs')]
            width = one(body,r'i64.const 128(?=\n\s*i64.or)','i64.const 0') if mode=='leb_target' else one(body,r'i64.store32 2\b' if mode=='overflow' else r'i64.store16 2\b','i64.store16 2' if mode=='overflow' else 'i64.store8 2')
            controls.append(('prefix',width,b'prefix conversion receiver image differs'))
            for label,changed,reason in controls:
                module=emit(run,validator,out,name+'-'+label,text[:a]+changed+text[z:],3)
                result=run(args+[module,mode],ok=False)
                assert result.returncode==1 and reason in result.stderr,(mode,label,result.stderr)
                count+=1
    return count


def check_failures(run,exe,cc,node,validator,wasmtime_python,out):
    count=0
    for amount,source_prefix,target_prefix in [(256,'u16','u8'),(65536,'u32','u16')]:
        source=f'fn main(){{var a:u8[{source_prefix}]=[73;{amount}];print("before");var b:u8[{target_prefix}]=copy(a);print("after");}}\n'
        path=out/f'prefix-conversion-range-{target_prefix}.goose';path.write_text(source)
        for opt in (0,2):
            prefix=out/f'prefix-conversion-range-{target_prefix}-O{opt}';c,native,module=(prefix.with_suffix(ext) for ext in ('.c','.native','.wasm'))
            run([exe,f'-O{opt}','--standalone','-o',c,path]);run([cc,f'-O{opt}',c,'-pthread','-lm','-ldl','-o',native]);result=run([native],ok=False)
            assert result.returncode and result.stdout==b'before\n' and b'array length exceeds storage range' in result.stderr,result.stderr
            run([exe,f'-O{opt}','--target','wasm','-o',module,path]);text=run([validator,'print',module]).stdout.decode()
            args=[node,ROOT/'test/wasm_array_prefix_conversion_failure.mjs']
            result=run(args+[emit(run,validator,out,prefix.name+'-healthy',text,3),amount]);assert result.stdout==b'before\n' and not result.stderr
            if wasmtime_python:
                result=run([wasmtime_python,ROOT/'test/wasmtime_host.py',module],ok=False)
                assert result.returncode==1 and result.stdout==b'before\n' and b'goose runtime error: array length exceeds stored prefix at ' in result.stderr
            count+=1;a,z=function_span(text,'main');body=text[a:z]
            changed=one(body,rf'i64.const {amount-1}\n(\s*)i64.gt_u',rf'i64.const {amount-1}\n\1i64.lt_u')
            result=run(args+[emit(run,validator,out,prefix.name+'-guard',text[:a]+changed+text[z:],3),amount],ok=False)
            assert result.returncode==1 and b'prefix conversion range executed after failure' in result.stderr,result.stderr;count+=1
    # This observer damages an exported count. It is not a native-valid value claim.
    for opt in (0,2):
        text=run([validator,'print',out/f'wasm_array_prefix_conversion_owner_overflow-O{opt}.wasm']).stdout.decode()
        args=[node,ROOT/'test/wasm_array_prefix_conversion_failure.mjs'];name=f'prefix-conversion-overflow-O{opt}'
        result=run(args+[emit(run,validator,out,name+'-healthy',text,3),'overflow']);assert result.stdout==b'before\n' and not result.stderr;count+=1
        a,z=function_span(text,'main');changed=one(text[a:z],r'i64.const 536870911\n(\s*)i64.gt_u',r'i64.const 536870911\n\1i64.lt_u')
        result=run(args+[emit(run,validator,out,name+'-guard',text[:a]+changed+text[z:],3),'overflow'],ok=False)
        assert result.returncode==1 and b'prefix conversion range executed after failure' in result.stderr,result.stderr;count+=1
    return count


def check_aggregate_prefix(run,exe,cc,node,validator,wasmtime_python,out):
    source='struct S{a:u8,b:i64,c:u16}fn main(){var a:S[u8]=[S{7,-8,900},S{9,10,800}];var b:S[u16]=copy(a);assert(b.len==2&&b[0].a==7&&b[0].b== -8&&b[0].c==900&&b[1].c==800);b[0].a=99;assert(a[0].a==7);print("padded");}\n'
    path=out/'prefix-conversion-aggregate.goose';path.write_text(source)
    for opt in (0,2):
        prefix=out/f'prefix-conversion-aggregate-O{opt}';c,native,module=(prefix.with_suffix(ext) for ext in ('.c','.native','.wasm'))
        run([exe,f'-O{opt}','--standalone','-o',c,path]);run([cc,f'-O{opt}',c,'-pthread','-lm','-ldl','-o',native]);result=run([native]);assert result.stdout==b'padded\n' and not result.stderr
        run([exe,f'-O{opt}','--target','wasm','-o',module,path]);run([validator,'validate',module])
        result=run([node,ROOT/'scripts/run_wasm.mjs',module]);assert result.stdout==b'padded\n' and not result.stderr
        if wasmtime_python:
            result=run([wasmtime_python,ROOT/'test/wasmtime_host.py',module]);assert result.stdout==b'padded\n' and not result.stderr
    return 2
