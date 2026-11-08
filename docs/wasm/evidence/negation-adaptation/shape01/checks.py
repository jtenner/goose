from pathlib import Path
import subprocess,json,hashlib,sys,re
p=Path(__file__).parent;raw=p.parent;r=Path('/home/dev/Projects/goose-wasm-backend');sys.path.insert(0,str(r/'test'));from wasm_data_iteration_checks import function_span
rows=[];proof=json.loads((raw/'focused04/results.json').read_text())
for opt in [0,2]:
 module=raw/'focused04'/f'function_data-O{opt}.wasm';row=next(x for x in proof if x['case']=='function_data' and x['opt']==opt);assert hashlib.sha256(module.read_bytes()).hexdigest()==row['wasm_sha256']
 a=subprocess.run(['wasm-tools','print',str(module)],capture_output=True)
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(f'print-O{opt}.'+k)).write_bytes(v)
 assert not a.returncode and a.stdout==(p/f'function_data-O{opt}.wat').read_bytes()
 s=a.stdout.decode();start,end=function_span(s,'run');head=s[start:end].splitlines()[0];params=re.search(r'\(param ([^)]+)\)',head)
 assert params and params[1].split()==['i64','i32'],head
 rows.append({'opt':opt,'header':head,'declared_goose_parameters':1,'wasm_parameters':2,'hidden_stack_base':True,'module_sha256':row['wasm_sha256']})
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS2 actual shared-call-context base-parameter shapes')
