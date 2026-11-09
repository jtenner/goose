"""Stored nonfixed sources: complete images and precise fault controls."""
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
        for mode,payload,source_top,target_kind in [
                ('grow_variable',24,25,'u16'),('grow_runtime',24,25,'runtime'),
                ('runtime_variable',24,49,'u16'),('runtime_grow',24,49,'grow'),
                ('grow_empty',0,1,'u16'),('runtime_empty',0,49,'u16'),
                ('grow_leb128',1024,1025,'leb')]:
            name=f'wasm_nonfixed_source_owner_{mode}-O{opt}'
            text=run([validator,'print',out/(name+'.wasm')]).stdout.decode()
            args=[node,ROOT/'test/wasm_nonfixed_source_owner.mjs'];record=out/(name+'.json')
            result=run(args+[emit(run,validator,out,name+'-healthy',text,3),mode,record])
            assert result.stdout==b'before\nafter\n' and not result.stderr;count+=1
            state=json.loads(record.read_text());a,z=function_span(text,'main');body=text[a:z]
            copy=r'(?:memory.copy 2 1|call \$goose.copy_memory)\b'
            length=rf'local.get \d+(?=\n\s*{copy})'
            controls=[
                ('long',one(body,length,f'i32.const {payload+1}'),b'nonfixed receiver image differs'),
                ('memory0',one(body,copy,lambda m:m[0]+f'\n      i32.const {state["initial"]+state["frameBytes"]+16}\n      i32.const 0\n      i32.store8'),b'nonfixed memory 0 image differs'),
                ('receiver-cleanup',one(body,r'global.set 2\b','drop'),b'nonfixed completed receiver top differs')]
            if source_top>1:
                controls.append(('source-cleanup',one(body,r'global.set 1\b','drop'),b'nonfixed completed source top differs'))
            if payload:
                controls.append(('short',one(body,length,f'i32.const {payload-1}'),b'nonfixed receiver image differs'))
                if 'memory.copy 2 1' in body:wrong=one(body,r'memory.copy 2 1\b','memory.copy 2 0')
                else:wrong=one(body,r'local.get \d+(?=\n\s*local.get \d+\n\s*call \$goose.copy_memory\b)','i64.const 0')
                controls.append(('source-memory',wrong,b'nonfixed receiver image differs'))
            if target_kind=='u16':wrong=one(body,r'i64.store16 2\b','i64.store8 2')
            elif target_kind=='runtime':wrong=one(body,r'i64.store32 2\b','i64.store16 2')
            elif target_kind=='leb':wrong=one(body,r'i64.const 128(?=\n\s*i64.or)','i64.const 0')
            else:wrong=None
            if wrong:controls.append(('prefix',wrong,b'nonfixed receiver image differs'))
            if mode.startswith('runtime_'):
                before_copy=re.search(copy,body).start();loads=list(re.finditer(r'i64.load32_u 1 offset=4\b',body[:before_copy]));assert loads
                load=loads[-1];wrong=body[:load.start()]+'i64.load32_u 1'+body[load.end():]
                controls.append(('capacity-is-not-length',wrong,b'nonfixed receiver top differs'))
            for label,changed,reason in controls:
                result=run(args+[emit(run,validator,out,name+'-'+label,text[:a]+changed+text[z:],3),mode],ok=False)
                assert result.returncode==1 and reason in result.stderr,(mode,label,result.stderr);count+=1
    return count


def check_guard(run,exe,cc,out):
    text='fn main(){var a:i64[>..]=[7,-8];var c:i64[>..]=[9];var refs:i64[>..]&[2]=[a,c];var b:i64[u16]=copy(refs[0]);assert(b.len==2&&b[0]==7&&b[1]== -8);refs[0].=c;assert(b[0]==7);print("grow_indexed_reference");}\n'
    source=out/'nonfixed-source-grow-reference-element.goose';source.write_text(text)
    for opt in (0,2):
        prefix=out/f'nonfixed-source-grow-reference-element-O{opt}';c,native,module=[prefix.with_suffix(ext) for ext in ['.c','.native','.wasm']]
        run([exe,f'-O{opt}','--standalone','-o',c,source]);run([cc,c,'-pthread','-lm','-ldl','-o',native]);result=run([native])
        assert result.stdout==b'grow_indexed_reference\n' and not result.stderr
        result=run([exe,f'-O{opt}','--target','wasm','-o',module,source],ok=False)
        assert result.returncode==1 and b'compound array elements need the pending layout lowering' in result.stderr and not module.exists(),result.stderr
    return 2


def check_dynamic(run,node,validator,out):
    count=0
    for opt in (0,2):
        name=f'wasm_nonfixed_source_owner_dynamic-O{opt}';text=run([validator,'print',out/(name+'.wasm')]).stdout.decode()
        args=[node,ROOT/'test/wasm_nonfixed_source_dynamic.mjs'];record=out/(name+'.json')
        result=run(args+[emit(run,validator,out,name+'-healthy',text,4),record])
        assert result.stdout==b'before\nafter\nbetween\nbefore\nafter\ndone\n' and not result.stderr;count+=1
        initial=json.loads(record.read_text())['initial'];a,z=function_span(text,'receive');body=text[a:z]
        length=r'local.get \d+(?=\n\s*call \$goose.copy_memory\b)'
        controls=[
            ('short',one(body,length,'i32.const 23'),b'nonfixed dynamic receiver image differs'),
            ('long',one(body,length,'i32.const 25'),b'nonfixed dynamic receiver image differs'),
            ('source-memory',one(body,r'local.get \d+(?=\n\s*local.get \d+\n\s*call \$goose.copy_memory\b)','i64.const 0'),b'nonfixed dynamic receiver image differs'),
            ('cleanup',one(body,r'call \$goose.restore_data\b','drop\n      drop'),b'nonfixed dynamic completed receiver top differs'),
            ('memory0',one(body,r'call \$goose.copy_memory\b',f'call $goose.copy_memory\n      i32.const {initial+16}\n      i32.const 0\n      i32.store8'),b'nonfixed dynamic memory 0 image differs')]
        for label,changed,reason in controls:
            result=run(args+[emit(run,validator,out,name+'-'+label,text[:a]+changed+text[z:],4)],ok=False)
            assert result.returncode==1 and reason in result.stderr,(label,result.stderr);count+=1
    return count


def range_program(kind):
    layout='[>..]' if kind=='grow' else '[..]'
    return f'fn main(){{var a:u8{layout}=[73;256];assert(a.len==256&&a[0]==73&&a[255]==73);print("before");var b:u8[u8]=copy(a);print("after");}}\n'


def check_failures(run,exe,cc,node,validator,wasmtime_python,out):
    count=0
    for kind in ['grow','runtime']:
        source=out/f'nonfixed-source-range-{kind}.goose';source.write_text(range_program(kind))
        for opt in (0,2):
            prefix=out/f'nonfixed-source-range-{kind}-O{opt}';c,native,module=[prefix.with_suffix(ext) for ext in ['.c','.native','.wasm']]
            run([exe,f'-O{opt}','--standalone','-o',c,source]);run([cc,c,'-pthread','-lm','-ldl','-o',native]);result=run([native],ok=False)
            assert result.returncode and result.stdout==b'before\n' and b'array length exceeds storage range' in result.stderr,result.stderr
            run([exe,f'-O{opt}','--target','wasm','-o',module,source]);text=run([validator,'print',module]).stdout.decode();args=[node,ROOT/'test/wasm_nonfixed_source_failure.mjs']
            result=run(args+[emit(run,validator,out,prefix.name+'-healthy',text,3),kind]);assert result.stdout==b'before\n' and not result.stderr
            if wasmtime_python:
                result=run([wasmtime_python,ROOT/'test/wasmtime_host.py',module],ok=False)
                assert result.returncode==1 and result.stdout==b'before\n' and b'goose runtime error: array length exceeds stored prefix at ' in result.stderr
            count+=1;a,z=function_span(text,'main');body=text[a:z]
            changed=one(body,r'i64.const 255\n(\s*)i64.gt_u',r'i64.const 255\n\1i64.lt_u')
            result=run(args+[emit(run,validator,out,prefix.name+'-guard',text[:a]+changed+text[z:],3),kind],ok=False)
            assert result.returncode==1 and b'nonfixed range executed after failure' in result.stderr,result.stderr;count+=1
    for opt in (0,2):
        name=f'wasm_nonfixed_source_owner_size-O{opt}';text=run([validator,'print',out/(name+'.wasm')]).stdout.decode();args=[node,ROOT/'test/wasm_nonfixed_source_failure.mjs']
        for mode in ['product','sum']:
            result=run(args+[emit(run,validator,out,name+'-'+mode+'-healthy',text,3),mode]);assert result.stdout==b'before\n' and not result.stderr;count+=1
            a,z=function_span(text,'main');body=text[a:z]
            if mode=='product':changed=one(body,r'i64.const 536870911\n(\s*)i64.gt_u',r'i64.const 536870911\n\1i64.lt_u')
            else:
                matches=list(re.finditer(r'i64.const 4294967295\n\s*i64.gt_u',body));assert len(matches)>=2;span=matches[-1]
                changed=body[:span.start()]+span[0].replace('i64.gt_u','i64.lt_u')+body[span.end():]
            result=run(args+[emit(run,validator,out,name+'-'+mode+'-guard',text[:a]+changed+text[z:],3),mode],ok=False)
            if mode=='product':assert result.returncode==1 and b'nonfixed size guard executed after failure' in result.stderr,result.stderr
            else:assert result.returncode==1 and b'RuntimeError' in result.stderr and b'out of bounds' in result.stderr,result.stderr
            count+=1
    return count
