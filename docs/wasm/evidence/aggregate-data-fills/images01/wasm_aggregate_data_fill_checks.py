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
        state=json.loads(record.read_text());a,z=function_span(text,'produce');body=text[a:z];copy=r'call \$goose.copy_memory\b'
        controls=[
            ('short',one(body,r'i32.const 11(?=\n\s*call \$goose.copy_memory\b)','i32.const 10'),b'data fill receiver image differs'),
            ('long',one(body,r'i32.const 11(?=\n\s*call \$goose.copy_memory\b)','i32.const 12'),b'data fill receiver image differs'),
            ('memory0',one(body,copy,lambda m:m[0]+f'\n      i32.const {state["initial"]+11}\n      i32.const 0\n      i32.store8'),b'data fill memory 0 image differs'),
            ('cleanup',one(body,r'call \$goose.restore_data\b','drop\n      drop'),b'data fill completed caller top differs')]
        # Replacing the source's high memory identity is checked separately
        # from receiver dispatch. The first copy argument remains unchanged.
        source=r'local.get \d+(?=\n\s*i64.extend_i32_u\n\s*i32.const 11\n\s*call \$goose.copy_memory\b)'
        controls.append(('source-memory',one(body,source,'i32.const 1'),b'data fill receiver image differs'))
        for label,changed,reason in controls:
            result=run(args+[emit(run,validator,out,name+'-'+label,text[:a]+changed+text[z:],3),'dynamic'],ok=False)
            assert result.returncode==1 and reason in result.stderr,(label,result.stderr);count+=1
    return count
