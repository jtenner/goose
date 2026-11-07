from pathlib import Path
import subprocess,json,hashlib
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;exe=p.parent/'goose-tested';rows=[];commands=[]
cases={}
for aggregate in [False,True]:
 for limited in [False,True]:
  name='array_'+('aggregate' if aggregate else 'scalar')+('_limited' if limited else '')+'_exit';elem='Cell' if aggregate else 'i64';arr='[..2]' if limited else '[2]';v=lambda n:'Cell { n: '+str(n)+' }' if aggregate else str(n)
  access='.n' if aggregate else ''
  cases[name]=('struct Cell { n: i64 }\n' if aggregate else '')+'struct S { values: '+elem+arr+' }\nvar target: S = S { values: ['+v(1)+','+v(2)+'] };\nrecursive fn run() -> i64 { target = S { values: ['+v(9)+', { return 7; '+v(8)+' }] }; return 0; }\nfn main() { assert(run() == 7); assert(target.values[0]'+access+' == 1); assert(target.values[1]'+access+' == 2); print("'+name+'"); }\n'
cases['data_exit']='struct Cell { n: i64 }\nrecursive fn run() -> i64 { var rows: Cell[] = [Cell { n:1 }, { return 7; Cell { n:8 } }]; return 0; }\nfn main() { assert(run() == 7); print("data_exit"); }\n'
cases['array_copies']='struct Cell { n: i64 }\nstruct S { values: Cell[..2] }\nfn main() { var old: Cell = Cell { n: 7 }; var target: S = S { values: [Cell { n:1 },Cell { n:2 }] }; target = S { values: [old,target.values[0]] }; assert(target.values[0].n == 7); assert(target.values[1].n == 1); print("array_copies"); }\n'
cases['nested_assignment']='struct S { a: i64, b: i64 }\nvar outer: S = S { a:1,b:2 };\nvar inner: S = S { a:3,b:4 };\nfn main() { outer = S { a:9, b: { inner = S { a:7, b: { assert(outer.a == 1); print("nested-live"); outer.a } }; assert(inner.a == 7); assert(inner.b == 1); assert(outer.a == 1); print("nested-done"); 8 } }; assert(outer.a == 9); assert(outer.b == 8); assert(inner.b == 1); print("nested_assignment"); }\n'
def run(stem,label,args):
 a=subprocess.run(list(map(str,args)),cwd=r,capture_output=True,timeout=90)
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:dest=p/(stem+'-'+label+'.'+ext);assert not dest.exists();dest.write_bytes(data)
 commands.append({'name':stem+'-'+label,'args':list(map(str,args)),'exit':a.returncode});(p/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');return a
for name,text in cases.items():
 source=p/(name+'.goose');source.write_text(text)
 expected=b'nested-live\nnested-done\nnested_assignment\n' if name=='nested_assignment' else (name+'\n').encode()
 for opt in [0,2]:
  stem=name+f'-O{opt}';c=p/(stem+'.c');native=p/(stem+'.native')
  for label,args in [('emit',[exe,f'-O{opt}','--standalone','-o',c,source]),('cc',['cc',c,'-pthread','-lm','-ldl','-o',native]),('native',[native])]:
   a=run(stem,label,args);assert not a.returncode,(name,label,a.stderr)
   if label=='native':assert a.stdout==expected and not a.stderr,(name,a.stdout,a.stderr)
  a=run(stem,'before',[exe,f'-O{opt}','--target','wasm','-o',p/(stem+'.wasm'),source])
  if name in ['array_copies','nested_assignment']:assert not a.returncode,(name,a.stderr)
  else:assert a.returncode==1 and (b'this value layout is not implemented (scalar backend)' in a.stderr or b'aggregate adaptation needs the pending destination lowering' in a.stderr),a.stderr
  rows.append({'case':name,'opt':opt,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'native':'PASS','wasm_before':'PASS' if not a.returncode else a.stderr.decode()});(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print('PASS:',len(rows),'native checks;10 confirmed array-element exit compilation failures,4 earlier candidate successes.')
