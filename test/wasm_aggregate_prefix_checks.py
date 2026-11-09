"""Fixed aggregate prefixes and canonical unused-slot images."""
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
        for label,prefix in [('u8',1),('u16',2),('u64',8)]:
            name=f'wasm_aggregate_prefix_owner_{label}-O{opt}';text=run([validator,'print',out/(name+'.wasm')]).stdout.decode()
            args=[node,ROOT/'test/wasm_aggregate_prefix_owner.mjs'];record=out/(name+'.json')
            result=run(args+[emit(run,validator,out,name+'-healthy',text,2),prefix,record]);assert result.stdout==b'before\nafter\n' and not result.stderr;count+=1
            state=json.loads(record.read_text());a,z=function_span(text,'main');body=text[a:z]
            header=r'i64.const 2(?=\n\s*local.set (\d+)\n\s*i32.wrap_i64\n\s*local.get \1\n\s*i64.store(?:8|16)? 1(?: align=1)?\n)'
            field=rf'i32.const {prefix+1}(?=\n\s*i32.add\n\s*i32.const 0\n\s*i32.add\n\s*i64.const 11\n\s*i64.store16 1)'
            controls=[
                ('count',one(body,header,'i64.const 3'),b'aggregate prefix data image differs'),
                ('field',one(body,field,f'i32.const {prefix+2}'),b'aggregate prefix data image differs'),
                ('zero',one(body,r'memory.fill 1\b','drop\n      drop\n      drop'),b'aggregate prefix data image differs'),
                ('long-zero',one(body,r'i32.const 6(?=\n\s*memory.fill 1\b)','i32.const 8'),b'aggregate prefix data image differs'),
                ('memory0',one(body,r'call \$goose.reserve_memory\.1\b',f'call $goose.reserve_memory.1\n      i32.const {state["initial"]+16}\n      i32.const 0\n      i32.store8'),b'aggregate prefix memory 0 image differs'),
                ('reserve',one(body,rf'i32.const {prefix+26}(?=\n\s*call \$goose.reserve_memory\.1\b)',f'i32.const {prefix+25}'),b'aggregate prefix live data top differs'),
                ('early',one(body,r'call \$goose.reserve_memory\.1\b','call $goose.reserve_memory.1\n      i32.const 1\n      global.set 1'),b'aggregate prefix live data top differs'),
                ('cleanup',one(body,r'global.set 1\b','drop'),b'aggregate prefix completed data top differs'),
            ]
            for kind,changed,reason in controls:
                result=run(args+[emit(run,validator,out,name+'-'+kind,text[:a]+changed+text[z:],2),prefix],ok=False)
                assert result.returncode==1 and reason in result.stderr,(label,kind,result.stderr);count+=1
    return count


def check_dynamic(run,node,validator,out):
    count=0
    for opt in (0,2):
        name=f'wasm_aggregate_prefix_owner_dynamic-O{opt}';text=run([validator,'print',out/(name+'.wasm')]).stdout.decode()
        args=[node,ROOT/'test/wasm_aggregate_prefix_dynamic.mjs']
        result=run(args+[emit(run,validator,out,name+'-healthy',text,3)]);assert result.stdout==b'before\nafter\nbefore\nafter\ndone\n' and not result.stderr;count+=1
        a,z=function_span(text,'produce');body=text[a:z];changed=one(body,r'call \$goose.fill_memory\b','drop\n      drop\n      drop')
        result=run(args+[emit(run,validator,out,name+'-zero',text[:a]+changed+text[z:],3)],ok=False)
        assert result.returncode==1 and b'aggregate dynamic data image differs' in result.stderr,result.stderr;count+=1
        match=re.search(r'(?m)^  \(func \$goose.fill_memory(?=\s|\()',text);assert match
        a=match.start();z=text.index('\n  )',a)+len('\n  )');changed=one(text[a:z],r'i64.const 32\b','i64.const 33')
        result=run(args+[emit(run,validator,out,name+'-memory',text[:a]+changed+text[z:],3)],ok=False)
        assert result.returncode==1 and b'aggregate dynamic memory 0 image differs' in result.stderr,result.stderr;count+=1
    return count


def check_guards(run,exe,cc,out):
    count=0
    programs={
        'grow':('struct S{n:i64}fn main(){var rows:S[>..]=[S{7}];assert(rows[0].n==7);print("guard");}\n',b'compound array elements need the pending layout lowering'),
        'runtime-fill':('struct S{n:i64}fn main(){var rows:S[..]=[S{7};2];assert(rows[1].n==7);print("guard");}\n',b'compound array elements need the pending layout lowering'),
    }
    for name,(text,reason) in programs.items():
        path=out/f'aggregate-prefix-guard-{name}.goose';path.write_text(text)
        for opt in (0,2):
            prefix=out/f'aggregate-prefix-guard-{name}-O{opt}';c,native,module=(prefix.with_suffix(ext) for ext in ('.c','.native','.wasm'))
            run([exe,f'-O{opt}','--standalone','-o',c,path]);run([cc,c,'-pthread','-lm','-ldl','-o',native]);result=run([native]);assert result.stdout==b'guard\n' and not result.stderr
            result=run([exe,f'-O{opt}','--target','wasm','-o',module,path],ok=False)
            assert result.returncode==1 and reason in result.stderr and not module.exists(),(name,result.stderr);count+=1
    return count
