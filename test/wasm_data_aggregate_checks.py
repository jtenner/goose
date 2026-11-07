"""Fresh aggregate data owners: spans, cleanup controls, and bounded scratch."""
import json,re
from pathlib import Path
from wasm_data_aggregate_controls import derive
ROOT=Path(__file__).resolve().parents[1]


def check_footprint(run,exe,cc,node,validator,wasmtime_python,out,local_counts):
    groups=0;observed={}
    for kind in ('limited-literal','fill-and-text','unknown'):
        for amount in (32,256):
            if kind=='fill-and-text':
                fields='mark: u8, cells: u16[2], text: u8[3], zero: u32[2] = default<u32[2]>(), tail: u8'
                value='Row { mark: 1, cells: [7; 2], text: "abc", tail: 2 }'
                checks='assert(row.mark == 1); assert(row.cells[0] == 7); assert(row.cells[1] == 7); assert(row.text[0] == 97); assert(row.text[2] == 99); assert(row.zero[0] == 0); assert(row.zero[1] == 0); assert(row.tail == 2);'
                image=bytes([1,7,0,7,0,97,98,99])+bytes(8)+bytes([2])
            else:
                fields='mark: u8, cells: u16[..3], tail: u8';value='Row { mark: 1, cells: [7, 8], tail: 2 }'
                checks='assert(row.mark == 1); assert(row.cells.len == 2); assert(row.cells[0] == 7); assert(row.cells[1] == 8); assert(row.tail == 2);'
                image=bytes([1,2,7,0,8,0,0,0,2])
            literal=', '.join([value]*amount)
            if kind=='unknown':
                body=('recursive fn make() -> i64 { var rows: Row[] = ['+literal+']; assert(rows.len == '+str(amount)+'); var i: i64 = 0; while i < rows.len { '+checks.replace('row.','rows[i].')+' i++; } return rows[rows.len - 1].cells[1]; }\n'
                      'fn main() { assert(make() == 8); var keep: i64[] = [91]; assert(make() == 8); assert(keep[0] == 91); print("scaling=ok"); }\n')
            else:body='fn main() { var rows: Row[] = ['+literal+']; assert(rows.len == '+str(amount)+'); for &row in rows { '+checks+' } print("scaling=ok"); }\n'
            source=out/f'data-footprint-{kind}-{amount}.goose';source.write_text('struct Row { '+fields+' }\n'+body)
            for opt in (0,2):
                prefix=out/f'data-footprint-{kind}-{amount}-O{opt}';c=prefix.with_suffix('.c');native=prefix.with_suffix('.native');module=prefix.with_suffix('.wasm')
                run([exe,f'-O{opt}','--standalone','-o',c,source]);run([cc,'-O0',c,'-pthread','-lm','-ldl','-o',native]);reference=run([native]);assert reference.stdout==b'scaling=ok\n' and not reference.stderr
                run([exe,f'-O{opt}','--target','wasm','-o',module,source]);run([validator,'validate',module])
                capture=out/(prefix.name+'-instance');actual=run([node,ROOT/'test/wasm_reference_abi.mjs',module,capture]);assert actual.stdout==reference.stdout and not actual.stderr;groups+=1
                for memory in ((1,2) if kind=='unknown' else (1,)):
                    actual_image=(capture/f'data_memory_{memory}.bin').read_bytes();model=bytes(1)+amount.to_bytes(4,'little')+image*amount;model=bytearray(model+bytes(len(actual_image)-len(model)))
                    if kind=='unknown' and memory==1:model[1:5]=(1).to_bytes(4,'little');model[5:13]=(91).to_bytes(8,'little')
                    assert actual_image==model,(kind,amount,opt,memory,'complete data image')
                if wasmtime_python:
                    actual=run([wasmtime_python,ROOT/'test/wasmtime_host.py',module]);assert actual.stdout==reference.stdout and not actual.stderr;groups+=1
                counts=local_counts(module.read_bytes());assert max(counts)<=80,(kind,amount,opt,counts)
                observed[(kind,amount,opt)]=counts
    for kind in ('limited-literal','fill-and-text','unknown'):
        for opt in (0,2):assert observed[kind,32,opt]==observed[kind,256,opt],(kind,opt,'constructor locals or helper count scales with literal length');groups+=1
    (out/'data-footprint-results.json').write_text(json.dumps([{'kind':k,'amount':n,'opt':o,'locals':v,'functions':len(v)} for (k,n,o),v in observed.items()],indent=2)+'\n')
    return groups


def check_controls(run,exe,cc,node,validator,wasmtime_python,out):
    groups=0
    def check(module,mode,expected,line=None):
        nonlocal groups
        engines=[[node,ROOT/'test/wasm_data_aggregate_reservation.mjs']]
        if wasmtime_python:engines.append([wasmtime_python,ROOT/'test/wasm_data_aggregate_reservation.py'])
        for index,engine in enumerate(engines):
            result=out/f'{module.stem}-{mode}-{index}.json';args=[*engine,module,mode,result]
            if line is not None:args.append(str(line))
            actual=run(args);assert actual.stdout==expected and not actual.stderr;assert json.loads(result.read_text())['allChecks']=='PASS';groups+=1
    for opt in (0,2):
        for kind,mode in [('growth','growth-failure'),('overflow','overflow')]:
            original=out/f'wasm_data_aggregate_{kind}-O{opt}.wasm';module=out/f'data-{kind}-control-O{opt}.wasm';module.write_bytes(derive(original.read_bytes(),kind=='growth'));run([validator,'validate',module]);check(module,mode,b'allocation-control=ok\n')
            if kind=='growth':
                healthy=out/f'data-growth-dirty-O{opt}.wasm';healthy.write_bytes(derive(original.read_bytes()));run([validator,'validate',healthy]);check(healthy,'growth-healthy',b'ready\nchild\nchild\ndone\n')
                if opt==0:
                    text=run([validator,'print',healthy]).stdout.decode();pattern=r'\bmemory\.fill\s+1\b';assert len(re.findall(pattern,text))==2
                    wat=out/'data-wrong-zero.wat';wat.write_text(re.sub(pattern,'memory.fill',text,count=1));damaged=wat.with_suffix('.wasm');run([validator,'parse',wat,'-o',damaged]);run([validator,'validate',damaged])
                    line=next(i for i,s in enumerate((ROOT/'test/wasm/wasm_data_aggregate_growth.goose').read_text().splitlines(),1) if 'assert(rows[0].bytes[39999]' in s);check(damaged,'growth-bad-zero',b'allocation-control=ok\n',line)
    text=(ROOT/'test/wasm/wasm_data_aggregate_cleanup.goose').read_text();assert text.count('[inner(1), inner(2)]')==1
    source=out/'data-wrong-order.goose';source.write_text(text.replace('[inner(1), inner(2)]','[inner(2), inner(1)]'));line=next(i for i,s in enumerate(text.splitlines(),1) if 'assert(trace == 1020305060709)' in s)
    for opt in (0,2):
        prefix=out/f'data-wrong-order-O{opt}';c=prefix.with_suffix('.c');native=prefix.with_suffix('.native');module=prefix.with_suffix('.wasm')
        run([exe,f'-O{opt}','--standalone','-o',c,source]);run([cc,'-O0',c,'-pthread','-lm','-ldl','-o',native]);run([exe,f'-O{opt}','--target','wasm','-o',module,source]);run([validator,'validate',module])
        engines=[[native],[node,ROOT/'scripts/run_wasm.mjs',module]]
        if wasmtime_python:engines.append([wasmtime_python,ROOT/'test/wasmtime_host.py',module])
        for engine in engines:
            actual=run(engine,ok=False);assert actual.returncode and b'assert' in actual.stderr.lower() and f'{source}:{line}'.encode() in actual.stderr and not actual.stdout;groups+=1
    return groups
