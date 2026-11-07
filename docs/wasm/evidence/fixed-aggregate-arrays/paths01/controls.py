from pathlib import Path
import sys,subprocess,json
sys.dont_write_bytecode=True
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');rows=[]
sys.path.insert(0,str(r/'test'));from wasm_aggregate_checks import check_controls
def run(args,*,ok=True):
 name='control-'+str(len(rows)).zfill(3);args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120)
 for ext,d in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]:
  with (p/(name+'.'+ext)).open('xb') as f:f.write(d)
 rows.append({'name':name,'command':args,'exit':a.returncode});(p/'control-results.json').write_text(json.dumps(rows,indent=2)+'\n')
 if ok and a.returncode:raise AssertionError((name,a.returncode,a.stderr))
 return a
n=check_controls(run,'node','wasm-tools','/tmp/goose-wasm-runtime-env/bin/python',p,source=p.parent/'control.goose',stem='control')
(p/'control-summary.json').write_text(json.dumps({'checks':n,'commands':len(rows),'passed':True},indent=2)+'\n');print(str(n)+' aggregate controls passed')
