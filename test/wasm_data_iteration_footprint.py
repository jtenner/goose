"""Static loop footprint across count and stride; no performance measurements."""
from pathlib import Path
import json,re
from wasm_data_iteration_checks import function_span
ROOT=Path(__file__).resolve().parents[1]


def check_footprint(run,exe,cc,node,validator,wasmtime_python,out,parent=None,correctness_only=False):
    p=out/'data-iteration-footprint';p.mkdir(exist_ok=True);rows=[];groups=0
    for stride in (1,7,16,256,40008):
        if stride==1:fields='';value='S {}';checks='';term='1'
        elif stride==7:fields='mark: u8, n: u32, tail: u16';value='S { mark: 11, n: 7, tail: 50001 }';checks='assert(s.mark == 11); assert(s.tail == 50001);';term='s.n'
        elif stride==16:fields='n: i64, tail: i64';value='S { n: 7, tail: 9 }';checks='assert(s.tail == 9);';term='s.n'
        else:
            payload=stride-8;fields=f'bytes: u8[{payload}], n: i64';value=f'S {{ bytes: [3; {payload}], n: 7 }}';checks=f'assert(s.bytes[0] == 3); assert(s.bytes[{payload-1}] == 3);';term='s.n'
        for amount in (0,1,32,256):
            source=p/f'rows-{stride}-{amount}.goose'
            source.write_text('struct S { '+fields+' }\nvar template: S = '+value+';\nvar values: S[] = ['+', '.join(['template']*amount)+'];\n'
                'recursive fn fold(rows: S[]&) -> i64 { var total: i64 = 0; for s, i in rows { assert(&s .!= &rows[i]); '+checks+' total += '+term+'; } return total; }\n'
                f'fn main() {{ assert(fold(values) == {amount*(1 if stride==1 else 7)}); print("footprint"); }}\n')
            for opt in (0,2):
                prefix=p/f'rows-{stride}-{amount}-O{opt}';c=prefix.with_suffix('.c');native=prefix.with_suffix('.native');module=prefix.with_suffix('.wasm')
                reference=parent if parent else exe
                run([reference,f'-O{opt}','--standalone','-o',c,source]);run([cc,'-O0',c,'-pthread','-lm','-ldl','-o',native]);actual=run([native]);assert actual.stdout==b'footprint\n' and not actual.stderr
                if parent:
                    rejected=prefix.with_suffix('.parent.wasm');actual=run([parent,f'-O{opt}','--target','wasm','-o',rejected,source],ok=False)
                    assert actual.returncode==1 and b'by-value aggregate iteration needs a fixed Memory 0 copy owner' in actual.stderr and not rejected.exists()
                run([exe,f'-O{opt}','--target','wasm','-o',module,source]);run([validator,'validate',module]);text=run([validator,'print',module]).stdout.decode();a,z=function_span(text,'fold');function=text[a:z]
                reserve=re.findall(r'i32.const (\d+)\s+call \$goose.reserve_frame',function);assert reserve==[str(stride)],(stride,amount,opt,reserve)
                loop=re.search(r'(?m)^\s*loop\b',function);assert loop
                assert 'call $goose.reserve_frame' not in function[loop.start():]
                assert function.count('call $goose.copy_to_frame')==1
                assert 'call $goose.reserve_memory' not in function
                memories=len(re.findall(r'(?m)^\s*\(memory\s',text));assert memories==2
                exports=''.join(f'  (export "test_stack_top_{i}" (global {i}))\n' for i in range(memories));wat=prefix.with_suffix('.owner.wat');wat.write_text(text[:text.rfind(')')]+exports+')\n');owner=prefix.with_suffix('.owner.wasm');run([validator,'parse',wat,'-o',owner]);run([validator,'validate',owner])
                actual=run([node,ROOT/'test/wasm_data_iteration_global.mjs',owner,str(stride),str(amount),prefix.with_suffix('.owner.json')]);assert actual.stdout==b'footprint\n' and not actual.stderr;groups+=1
                if wasmtime_python:
                    actual=run([wasmtime_python,ROOT/'test/wasmtime_host.py',module]);assert actual.stdout==b'footprint\n' and not actual.stderr;groups+=1
                row={'stride':stride,'amount':amount,'opt':opt,'complete_images':'PASS'}
                if not correctness_only:
                    locals_=sum(len(re.findall(r'\b(?:i32|i64|f32|f64)\b',x)) for x in re.findall(r'\(local ([^)]+)\)',function))
                    row.update(binder_bytes=stride,loop_locals=locals_,loop_copy_sites=1,
                               functions=len(re.findall(r'(?m)^  \(func ',text)),module_bytes=module.stat().st_size)
                rows.append(row)
                (p/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
    if correctness_only:
        return groups
    for stride in (1,7,16,256,40008):
        for opt in (0,2):
            cases=[x for x in rows if x['stride']==stride and x['opt']==opt]
            assert len(cases)==4 and len({x['loop_locals'] for x in cases})==1 and len({x['functions'] for x in cases})==1,cases
            groups+=1
    return groups
