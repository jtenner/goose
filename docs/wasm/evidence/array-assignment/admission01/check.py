from pathlib import Path
import sys,subprocess,json
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;sys.path.insert(0,str(r/'test'));import wasm_aggregate_admission as c
c.CASES={'array-assign':c.CASES['array-assign']};commands=[]
def run(args,ok=True):
 a=subprocess.run(list(map(str,args)),cwd=r,capture_output=True,timeout=90);stem=p/f'command{len(commands):03}'
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:stem.with_suffix('.'+ext).write_bytes(data)
 commands.append({'args':list(map(str,args)),'exit':a.returncode});(p/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 if ok:assert not a.returncode,(args,a.stderr)
 return a
print(c.check_admission(run,p.parent/'goose-tested','cc',p,'node','wasm-tools',Path('/tmp/goose-wasm-runtime-env/bin/python')))
