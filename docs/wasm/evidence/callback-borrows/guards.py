from pathlib import Path
import subprocess,json,sys
r=Path(__file__).parent;repo=Path('/home/dev/Projects/goose-wasm-backend');out=r/'guards01';out.mkdir(exist_ok=True);sys.path.insert(0,str(repo/'test'));from wasm_callback_borrow_checks import check_guards
serial=0
def run(args,ok=True):
 global serial
 serial+=1;args=list(map(str,args));a=subprocess.run(args,cwd=repo,capture_output=True,timeout=120);p=out/f'command-{serial:04}';p.with_suffix('.json').write_text(json.dumps(args)+'\n');p.with_suffix('.stdout').write_bytes(a.stdout);p.with_suffix('.stderr').write_bytes(a.stderr);p.with_suffix('.exit').write_text(str(a.returncode)+'\n')
 if ok:assert not a.returncode,(args,a.returncode,a.stderr)
 return a
identity=json.loads((r/'compiler-identity.json').read_text());n=check_guards(run,identity['compiler'],'cc',out);assert n==4;print('PASS',n,'native-valid callback reference-result guards')
