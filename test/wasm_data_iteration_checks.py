"""Live binder images, bounded copies and cleanup for data-array iteration."""
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
MODES={'control':'copy','zero_control':'zero','checkpoint':'cleanup','enum_image':'enum','inline_image':'inline'}


def function_span(text,prefix):
    matches=list(re.finditer(r'(?m)^  \(func \$'+re.escape(prefix)+r'\.\d+(?=\s|\()',text))
    assert len(matches)==1,(prefix,'function not unique')
    start=matches[0].start();end=text.find('\n  (func ',start+1)
    assert end>start,(prefix,'function end not found')
    return start,end


def check_modules(run,node,validator,wasmtime_python,out):
    count=0;facts=[]
    def module(name,text):
        wat=out/(name+'.wat');wasm=wat.with_suffix('.wasm');wat.write_text(text)
        run([validator,'parse',wat,'-o',wasm]);run([validator,'validate',wasm]);return wasm
    def owner(name,text,mode,expected,reason=None):
        nonlocal count
        wasm=module(name,text);record=out/(name+'-owner.json')
        result=run([node,ROOT/'test/wasm_data_iteration_owner.mjs',wasm,mode,record],ok=reason is None)
        assert result.stdout==expected,(name,result.stdout)
        if reason:assert result.returncode==1 and reason in result.stderr,(name,result.stderr)
        else:assert not result.stderr and json.loads(record.read_text())['complete']
        count+=1
    def failure(name,text,source,assertion,expected=b''):
        nonlocal count
        wasm=module(name,text);line=next(i for i,s in enumerate(source.read_text().splitlines(),1) if assertion in s)
        engines=[[node,ROOT/'scripts/run_wasm.mjs',wasm]]
        if wasmtime_python:engines.append([wasmtime_python,ROOT/'test/wasmtime_host.py',wasm])
        for args in engines:
            result=run(args,ok=False);assert result.returncode==1 and b'assert failed' in result.stderr and f'{source}:{line}'.encode() in result.stderr,(name,result.stderr)
            assert result.stdout==expected,(name,result.stdout);count+=1
    for opt in (0,2):
        texts={};owners={}
        for kind,mode in MODES.items():
            stem='wasm_data_aggregate_iteration_'+kind;text=run([validator,'print',out/f'{stem}-O{opt}.wasm']).stdout.decode();assert 'test_stack_top_' not in text
            memories=len(re.findall(r'(?m)^\s*\(memory\s',text));assert memories>=2
            exports=''.join(f'  (export "test_stack_top_{i}" (global {i}))\n' for i in range(memories))
            derived=text[:text.rfind(')')]+exports+')\n'
            expected=(ROOT/'test/expected'/(stem+'.out')).read_bytes();owner(f'data-iteration-{kind}-O{opt}',derived,mode,expected)
            texts[kind]=text;owners[kind]=derived
        source=ROOT/'test/wasm/wasm_data_aggregate_iteration_control.goose';text=texts['control'];a,z=function_span(text,'main');main=text[a:z]
        loop=re.search(r'(?m)^\s*loop\b[^\n]*\n',main);assert loop
        copies=list(re.finditer(r'(?m)^\s*memory\.copy 0 1[^\n]*\n',main));assert len(copies)==1
        copy=copies[0];prefix=main[loop.end():copy.start()]
        length=list(re.finditer(r'i32.const 7(?=\s+local.set \d+)',prefix));assert len(length)==1,'copy length not unique'
        at=loop.end()+length[0].start();end=loop.end()+length[0].end()
        def length_text(base,value):
            b,c=function_span(base,'main');body=base[b:c];assert body[at:end]=='i32.const 7'
            return base[:b]+body[:at]+f'i32.const {value}'+body[end:]+base[c:]
        failure(f'data-short-O{opt}',length_text(text,6),source,'assert(s.tail')
        owner(f'data-long-O{opt}',length_text(owners['control'],8),'copy',b'',b'iteration copy crossed its planned owner image')
        stride=list(re.finditer(r'i64.const 7(?=\s+i64.mul)',prefix));assert len(stride)==1
        at_stride=loop.end()+stride[0].start();end_stride=loop.end()+stride[0].end();broken=main[:at_stride]+'i64.const 8'+main[end_stride:]
        failure(f'data-stride-O{opt}',text[:a]+broken+text[z:],source,'assert(s.mark',b'iteration\n')
        broken=main[:copy.start()]+main[copy.start():copy.end()].replace('memory.copy 0 1','memory.copy')+main[copy.end():]
        failure(f'data-memory-O{opt}',text[:a]+broken+text[z:],source,'assert(s.mark')
        broken=main[:copy.start()]+main[copy.start():copy.end()].replace('memory.copy 0 1','drop\n      drop\n      drop')+main[copy.end():]
        failure(f'data-omitted-O{opt}',text[:a]+broken+text[z:],source,'assert(s.mark')
        zero=owners['zero_control'];b,c=function_span(zero,'empty');body=zero[b:c];head=re.search(r'(?m)^\s*loop\b[^\n]*\n',body);assert head
        branch=re.search(r'(?m)^\s*br_if[^\n]*\n',body[head.end():]);assert branch;guard_end=head.end()+branch.end()
        calls=list(re.finditer(r'(?m)^\s*call \$goose\.copy_to_frame[^\n]*\n',body));assert len(calls)==1 and calls[0].start()>guard_end
        copy_end=calls[0].end();hoisted=body[:head.end()]+body[guard_end:copy_end]+body[head.end():guard_end]+body[copy_end:]
        owner(f'data-eager-O{opt}',zero[:b]+hoisted+zero[c:],'zero',b'',b'zero-trip iteration copied an element')
        cleanup=owners['checkpoint'];b,c=function_span(cleanup,'main');body=cleanup[b:c];assert body.count('global.set 3')>=1
        broken=body.replace('global.set 3','drop',1)
        owner(f'data-cleanup-O{opt}',cleanup[:b]+broken+cleanup[c:],'cleanup',b'inner\n',b'iteration body data top was not restored at its completion')
        facts.append({'opt':opt,'unique_loop_copy':True,'length_site':7,'source_memory':1,'mutations_validated':7,'healthy_owner_modes':len(MODES)})
    (out/'data-iteration-control-facts.json').write_text(json.dumps(facts,indent=2)+'\n')
    return count


def check_recursion(run,node,validator,wasmtime_python,out):
    source=ROOT/'test/wasm/wasm_data_aggregate_iteration_recursion.goose'
    line=next(i for i,s in enumerate(source.read_text().splitlines(),1) if 'assert(&s .!= parent)' in s)
    expected=(ROOT/'test/expected/wasm_data_aggregate_iteration_recursion.out').read_bytes()
    count=0
    for opt in (0,2):
        text=run([validator,'print',out/f'wasm_data_aggregate_iteration_recursion-O{opt}.wasm']).stdout.decode()
        frames={}
        for name in ('main','walk'):
            a,z=function_span(text,name)
            reserve=re.findall(r'i32.const (\d+)\s+call \$goose.reserve_frame\s+local.set \d+',text[a:z])
            assert len(reserve)==1,(name,reserve)
            frames[name]=int(reserve[0])
        initial=re.findall(r'\(global \(;0;\) \(mut i32\) i32.const (\d+)\)',text)
        assert len(initial)==1
        derived=text[:text.rfind(')')]+'  (export "test_stack_top_0" (global 0))\n)\n'
        wat=out/f'data-recursion-owner-O{opt}.wat';wat.write_text(derived);module=wat.with_suffix('.wasm')
        run([validator,'parse',wat,'-o',module]);run([validator,'validate',module])
        result=run([node,ROOT/'test/wasm_data_iteration_recursion.mjs',module,str(frames['main']),str(frames['walk'])])
        assert result.stdout==expected and not result.stderr
        count+=1
        a,z=function_span(text,'walk');body=text[a:z]
        # Reserve distinct live regions, but deliberately make every activation use the first frame.
        shared=int(initial[0])+frames['main']
        body,n=re.subn(r'(call \$goose.reserve_frame\s+)(local.set \d+)',
                       lambda m:m[1]+f'drop\n    i32.const {shared}\n    '+m[2],body,count=1)
        assert n==1
        wat=out/f'data-recursion-shared-frame-O{opt}.wat';wat.write_text(text[:a]+body+text[z:]);module=wat.with_suffix('.wasm')
        run([validator,'parse',wat,'-o',module]);run([validator,'validate',module])
        engines=[[node,ROOT/'scripts/run_wasm.mjs',module]]
        if wasmtime_python:engines.append([wasmtime_python,ROOT/'test/wasmtime_host.py',module])
        for args in engines:
            result=run(args,ok=False)
            assert result.returncode==1 and b'assert failed' in result.stderr and f'{source}:{line}'.encode() in result.stderr,result.stderr
            assert result.stdout==b'enter=3\n',result.stdout
            count+=1
    return count
