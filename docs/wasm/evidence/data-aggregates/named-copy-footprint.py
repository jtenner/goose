from pathlib import Path
import hashlib,json,subprocess,sys
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(sys.argv[1]);exe=Path(sys.argv[2]);rows=[];commands=[]
sys.path.insert(0,str(r/'test'));from wasm_backend import function_local_counts

def run(name,args):
 a=subprocess.run([str(x) for x in args],cwd=r,capture_output=True,timeout=120)
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:(p/(name+'.'+ext)).write_bytes(data)
 commands.append({'name':name,'args':[str(x) for x in args],'exit':a.returncode});(p/'commands-results.json').write_text(json.dumps(commands,indent=2)+'\n')
 assert a.returncode==0,(name,a.stderr.decode(errors='replace'));return a
for kind in ['direct','nested']:
 for binding in ['local','global']:
  for base in ['known','unknown']:
   for amount in [32,256]:
    declarations='struct Item { a: u16, b: u16 }\n';template='var template: Item = Item { a: 7, b: 9 };\n'
    if kind=='nested':declarations+='struct Row { head: u8, payload: Item, tail: u8 }\n'
    owner='Item' if kind=='direct' else 'Row';value='template' if kind=='direct' else 'Row { head: 3, payload: template, tail: 5 }';field='' if kind=='direct' else '.payload';stride=4 if kind=='direct' else 6
    checks=f'assert(rows.len == {amount}); for &row in rows {{ assert(row{field}.a == 7); assert(row{field}.b == 9); }} rows[0]{field}.a = 17; assert(template.a == 7); assert(rows[rows.len - 1]{field}.a == 7);'
    body=(template if binding=='local' else '')+f'var rows: {owner}[] = ['+', '.join([value]*amount)+']; '+checks
    if base=='known':body='fn main() { '+body+' print("named-copy=ok"); }\n'
    else:body='recursive fn make() -> i64 { '+body+f' return rows[0]{field}.a; }}\nfn main() {{ assert(make() == 17); var keep: i64[] = [91]; assert(make() == 17); assert(keep[0] == 91); print("named-copy=ok"); }}\n'
    source=p/f'{kind}-{binding}-{base}-{amount}.goose';source.write_text(declarations+(template if binding=='global' else '')+body)
    for opt in [0,2]:
     name=source.stem+f'-O{opt}';c=p/(name+'.c');native=p/(name+'.native');module=p/(name+'.wasm');expected=b'named-copy=ok\n'
     run(name+'-native-emit',[exe,f'-O{opt}','--standalone','-o',c,source]);run(name+'-native-build',['cc','-O0',c,'-pthread','-lm','-ldl','-o',native]);a=run(name+'-native',[native]);assert a.stdout==expected and not a.stderr
     run(name+'-emit',[exe,f'-O{opt}','--target','wasm','-o',module,source]);run(name+'-validate',['wasm-tools','validate',module]);capture=p/(name+'-instance');a=run(name+'-node',['node',r/'test/wasm_reference_abi.mjs',module,capture]);assert a.stdout==expected and not a.stderr
     a=run(name+'-wasmtime',['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',module]);assert a.stdout==expected and not a.stderr
     item=bytes([7,0,9,0]);image=item if kind=='direct' else bytes([3])+item+bytes([5]);first=bytearray(image);first[0 if kind=='direct' else 1]=17
     for memory in ([1,2] if base=='unknown' else [1]):
      actual=(capture/f'data_memory_{memory}.bin').read_bytes();model=bytearray(bytes(1)+amount.to_bytes(4,'little')+first+image*(amount-1))
      if base=='unknown' and memory==1:model[1:5]=(1).to_bytes(4,'little');model[5:13]=(91).to_bytes(8,'little')
      model.extend(bytes(len(actual)-len(model)));assert actual==model,(name,memory,'full independent byte model')
     state=json.loads((capture/'instance.json').read_text());assert state['completionCalls']==1 and state['pendingPrints']==state['pendingSnapshots']==0
     counts=function_local_counts(module.read_bytes());rows.append({'kind':kind,'binding':binding,'base':base,'amount':amount,'opt':opt,'locals':counts,'functions':len(counts),'module_bytes':module.stat().st_size,'module_sha256':hashlib.sha256(module.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'all_behavior_and_models':'PASS'})
     (p/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
failures=[]
for kind in ['direct','nested']:
 for binding in ['local','global']:
  for base in ['known','unknown']:
   for opt in [0,2]:
    pair=[x for x in rows if (x['kind'],x['binding'],x['base'],x['opt'])==(kind,binding,base,opt)]
    if pair[0]['locals']!=pair[1]['locals']:failures.append({'kind':kind,'binding':binding,'base':base,'opt':opt,'locals32':pair[0]['locals'],'locals256':pair[1]['locals']})
result={'constant_copy_scratch':not failures,'cases':len(rows),'native_cases':len(rows),'Node_cases':len(rows),'Wasmtime_cases':len(rows),'failures':failures};(p/'footprint-assertion.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert not failures,'Named-copy scratch grows with literal length.'
