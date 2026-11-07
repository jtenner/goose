from pathlib import Path
import subprocess,json
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;exe=Path('/tmp/goose-wasm-inline-ref-abi-20261107/build04/goose-tested');source=r/'test/wasm/wasm_data_aggregate_mixed.goose';expected=(r/'test/expected/wasm_data_aggregate_mixed.out').read_bytes();results=[]
for opt in [0,2]:
 name='mixed-O'+str(opt);c=p/(name+'.c');native=p/(name+'.native')
 for step,args in [('emit',[exe,'-O'+str(opt),'--standalone','-o',c,source]),('build',['cc','-O0',c,'-pthread','-lm','-ldl','-o',native]),('run',[native])]:
  a=subprocess.run([str(x) for x in args],cwd=r,capture_output=True,timeout=120)
  for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:(p/(name+'-'+step+'.'+ext)).write_bytes(data)
  results.append({'name':name+'-'+step,'args':[str(x) for x in args],'exit':a.returncode});(p/'byte-commands.json').write_text(json.dumps(results,indent=2)+'\n');assert a.returncode==0,(name,step,a.stderr.decode(errors='replace'))
  if step=='run':assert a.stdout==expected and not a.stderr,(name,a.stdout,a.stderr)
print('New mixed-field fixture passes2native parent references.')
