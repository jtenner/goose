"""Complete data-fill images, snapshots, identities and precise fault controls."""
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
        for mode in ['u8_count3','u16_count3','u32_count3','u64_count3','u8_count0']:
            name=f'wasm_aggregate_data_fill_image_{mode}-O{opt}'
            text=run([validator,'print',out/(name+'.wasm')]).stdout.decode()
            args=[node,ROOT/'test/wasm_aggregate_data_fill_image.mjs'];record=out/(name+'.json')
            result=run(args+[emit(run,validator,out,name+'-healthy',text,2),mode,record])
            assert result.stdout==b'before\neval\nafter\n' and not result.stderr;count+=1
            state=json.loads(record.read_text());a,z=function_span(text,'main');body=text[a:z]
            value=re.search(r'call \$value\.\d+\b',body);assert value
            controls=[
                ('no-eval',body[:value.start()]+'i64.const -8'+body[value.end():],b'data fill initializer checkpoint differs'),
                ('twice',body[:value.start()]+value[0]+'\n      drop\n      '+value[0]+body[value.end():],b'data fill evaluation stage differs'),
                ('snapshot-cleanup',one(body,r'global.set 0\b','drop'),b'data fill snapshot restore differs'),
                ('receiver-cleanup',one(body,r'global.set 1\b','drop'),b'data fill final data top differs')]
            # At eval the complete receiver exists but no payload copy has run.
            width=state['prefix']*8;replacement=16 if width==8 else width//2
            controls.append(('prefix',one(body,rf'i64.store{width if width<64 else ""} 1\b',f'i64.store{replacement} 1'),b'data fill receiver image differs'))
            if state['count']:
                copy=r'memory.copy 1 0\b'
                for label,size in [('short',10),('long',12)]:
                    controls.append((label,one(body,r'i32.const 11(?=\n\s*memory.copy 1 0\b)',f'i32.const {size}'),b'data fill receiver image differs'))
                controls.append(('source-memory',one(body,copy,'memory.copy 1 1'),b'data fill receiver image differs'))
                before=re.search(copy,body).start();offsets=list(re.finditer(rf'i64.const {state["prefix"]}\n\s*i64.add\n\s*local.set \d+',body[:before]));assert offsets
                offset=offsets[-1];changed=body[:offset.start()]+one(offset[0],rf'i64.const {state["prefix"]}\b',f'i64.const {state["prefix"]+1}')+body[offset.end():]
                controls.append(('offset',changed,b'data fill receiver image differs'))
                controls.append(('memory0',one(body,copy,lambda m:m[0]+f'\n      i32.const {state["initial"]+11}\n      i32.const 0\n      i32.store8'),b'data fill memory 0 image differs'))
            for label,changed,reason in controls:
                result=run(args+[emit(run,validator,out,name+'-'+label,text[:a]+changed+text[z:],2),mode],ok=False)
                assert result.returncode==1 and reason in result.stderr,(mode,label,result.stderr);count+=1
    return count


def check_dynamic(run,node,validator,out):
    count=0
    for opt in (0,2):
        name=f'wasm_aggregate_data_fill_image_dynamic-O{opt}'
        text=run([validator,'print',out/(name+'.wasm')]).stdout.decode();args=[node,ROOT/'test/wasm_aggregate_data_fill_image.mjs'];record=out/(name+'.json')
        result=run(args+[emit(run,validator,out,name+'-healthy',text,3),'dynamic',record]);assert result.stdout==b'before\neval\nafter\nbetween\nbefore\neval\nafter\ndone\n' and not result.stderr;count+=1
        state=json.loads(record.read_text());a,z=function_span(text,'produce');body=text[a:z];copy=r'call \$goose.copy_from_frame\b'
        controls=[
            ('short',one(body,r'i32.const 11(?=\n\s*call \$goose.copy_from_frame\b)','i32.const 10'),b'data fill receiver image differs'),
            ('long',one(body,r'i32.const 11(?=\n\s*call \$goose.copy_from_frame\b)','i32.const 12'),b'data fill receiver image differs'),
            ('memory0',one(body,copy,lambda m:m[0]+f'\n      i32.const {state["initial"]+11}\n      i32.const 0\n      i32.store8'),b'data fill memory 0 image differs'),
            ('cleanup',one(body,r'call \$goose.restore_data\b','drop\n      drop'),b'data fill completed caller top differs')]
        source=r'local.get \d+(?=\n\s*i32.const 11\n\s*call \$goose.copy_from_frame\b)'
        controls.append(('source-address',one(body,source,f'i32.const {state["initial"]+12}'),b'data fill receiver image differs'))
        destination=r'local.get \d+(?=\n\s*local.get \d+\n\s*i32.const 11\n\s*call \$goose.copy_from_frame\b)'
        changed=one(body,destination,lambda m:m[0]+'\n      i64.const 4294967295\n      i64.and\n      i64.const 4294967296\n      i64.or')
        controls.append(('destination-memory',changed,b'data fill receiver image differs'))
        for label,changed,reason in controls:
            result=run(args+[emit(run,validator,out,name+'-'+label,text[:a]+changed+text[z:],3),'dynamic'],ok=False)
            assert result.returncode==1 and reason in result.stderr,(label,result.stderr);count+=1
    return count


def check_limits(run,exe,cc,node,validator,wasmtime_python,out):
    count=0
    cases=[('last-extent',4294967287,None),
           ('extent-over',4294967288,b'aggregate data literal exceeds memory32'),
           ('sentinel-count',4294967295,b'aggregate data fill needs a nonnegative memory32 count'),
           ('wide-count',4294967296,b'aggregate data fill needs a nonnegative memory32 count')]
    for name,length,reason in cases:
        # Recursive prevents compile-time inlining of the false flag. No large
        # allocation executes in native code or either Wasm engine.
        text=f'struct S{{n:u8}}recursive fn gated(flag:bool){{if flag{{var a:S[u64]=[S{{7}};{length}];assert(a.len=={length});}}}}fn main(){{gated(false);print("guard");}}\n'
        source=out/('data-fill-limit-'+name+'.goose');source.write_text(text)
        for opt in (0,2):
            prefix=out/f'data-fill-limit-{name}-O{opt}';c,native,module=[prefix.with_suffix(e) for e in ['.c','.native','.wasm']]
            run([exe,f'-O{opt}','--standalone','-o',c,source]);run([cc,f'-O{opt}',c,'-pthread','-lm','-ldl','-o',native]);result=run([native]);assert result.stdout==b'guard\n' and not result.stderr
            result=run([exe,f'-O{opt}','--target','wasm','-o',module,source],ok=False)
            if reason:
                assert result.returncode==1 and reason in result.stderr and not module.exists(),(name,opt,result.stderr)
            else:
                assert result.returncode==0 and not result.stderr,(name,opt,result.stderr)
                run([validator,'validate',module])
                result=run([node,ROOT/'test/wasm_reference_abi.mjs',module,out/f'data-fill-limit-{name}-O{opt}-instance']);assert result.stdout==b'guard\n' and not result.stderr
                result=run([node,ROOT/'test/wasm_multimemory.mjs',module,'0']);assert result.stdout==b'guard\n' and not result.stderr
                if wasmtime_python:
                    result=run([wasmtime_python,ROOT/'test/wasmtime_host.py',module]);assert result.stdout==b'guard\n' and not result.stderr
            count+=1
    return count
