from pathlib import Path
import subprocess,json
p=Path(__file__).parent;old=p.parent/'compatibility01';rows=[]
for entry in json.loads((old/'prior-module-summary.json').read_text()):
 if entry['identical']:continue
 stem=Path(entry['source']).stem+'-O'+str(entry['opt'])
 for label in ['before','after']:
  name=stem+'-'+label;a=subprocess.run(['wasm-tools','print',str(old/(name+'.wasm'))],capture_output=True,timeout=60)
  for ext,d in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]:
   with (p/(name+'.'+ext)).open('xb') as f:f.write(d)
  assert not a.returncode,(name,a.stderr);rows.append({'name':name,'exit':a.returncode})
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(str(len(rows))+' saved module dumps complete')
