"""Verify observed completed prefix; rerun corrected admission and every suffix."""
from pathlib import Path
import ast,copy,hashlib,json,shutil,sys,importlib.util,builtins
p=Path(__file__).parent;raw=p.parent;r=Path('/home/dev/Projects/goose-wasm-backend');old=raw/'full-correctness01';out=p/'artifacts';out.mkdir(exist_ok=True)
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
assert (old/'check.exit').read_text().strip()=='1'
error=(old/'check.stderr').read_text();assert "AssertionError: ('data-varint', 0, b'')" in error and 'check_aggregate_admission' in error
state=json.loads((old/'failure-state.json').read_text());assert state['completed_checks']==6243 and state['line']==415
original=json.loads((old/'validation-inputs.json').read_text());inputs=json.loads((raw/'validation-inputs.json').read_text());assert {n for n,h in original.items() if inputs[n]!=h}=={'test/wasm_aggregate_admission.py'}
for n,h in inputs.items():assert sha(r/n)==h,n
for n,h in json.loads((raw/'build01/source-hashes.json').read_text()).items():assert sha(r/n)==h,n
identity=json.loads((raw/'compiler-identity.json').read_text());assert sha(identity['compiler'])==identity['sha256']
assert (r/'test/wasm_backend.py').read_bytes()==(old/'wasm_backend.snapshot.py').read_bytes()
previous=json.loads((old/'fixture-reuse.json').read_text());assert previous['fixture_pairs']==2044
for rec in previous['fixtures']:
 module=old/'artifacts'/Path(rec['module']).name;assert sha(module)==rec['sha256'];assert sha(r/rec['source'])==inputs[rec['source']]
for f in (old/'artifacts').glob('*.wasm'):shutil.copy2(f,out/f.name)
sys.path.insert(0,str(r/'test'));spec=importlib.util.spec_from_file_location('wasm_backend',r/'test/wasm_backend.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
tree=ast.parse((r/'test/wasm_backend.py').read_text());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');start=next(i for i,n in enumerate(main.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='count' for t in n.targets));failed=next(i for i,n in enumerate(main.body) if isinstance(n,ast.AugAssign) and any(isinstance(v,ast.Call) and isinstance(v.func,ast.Name) and v.func.id=='check_aggregate_admission' for v in ast.walk(n)));assert main.body[failed].lineno==state['line']
imports=[copy.deepcopy(n) for n in main.body[start+1:failed] if isinstance(n,(ast.Import,ast.ImportFrom))]
setup=copy.deepcopy(main.body[:start+1])+imports
suffix=copy.deepcopy(main.body[failed:])
def names_stored(nodes):
 names={n.id for root in nodes for n in ast.walk(root) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store)}
 for root in nodes:
  for n in ast.walk(root):
   if isinstance(n,ast.ImportFrom):names.update(a.asname or a.name for a in n.names)
   if isinstance(n,ast.Import):names.update(a.asname or a.name.split('.')[0] for a in n.names)
 return names
loads={n.id for root in suffix for n in ast.walk(root) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Load)}
missing=loads-names_stored(setup+suffix)-set(m.__dict__)-set(dir(builtins));assert not missing,missing
proof={'status':'verified prefix only; suffix not complete','basis':'full-correctness01 observed failure at check_aggregate_admission after6243 returned main checks; only failing helper changed; original main and all prior input hashes unchanged','completed_prefix_checks':6243,'fixture_pairs':2044,'compiler_sha256':identity['sha256'],'fixtures':previous['fixtures']}
def save():
 (p/'prefix-reuse.json').write_text(json.dumps(proof,indent=2)+'\n');print('Verified and reused6243 completed checks; corrected admission and every later helper run fresh',flush=True)
m.save_prefix=save
main.body=setup+[ast.Assign([ast.Name('count',ast.Store())],ast.Constant(6243)),ast.Expr(ast.Call(ast.Name('save_prefix',ast.Load()),[],[]))]+suffix
exec(compile(ast.fix_missing_locations(ast.Module([main],type_ignores=[])),str(r/'test/wasm_backend.py'),'exec'),m.__dict__);sys.argv=[str(r/'test/wasm_backend.py'),*sys.argv[1:]]
try:m.main()
except BaseException as e:
 tb=e.__traceback__;state={}
 while tb:
  if tb.tb_frame.f_code.co_name=='main':state={'completed_checks':tb.tb_frame.f_locals.get('count'),'line':tb.tb_lineno,'exception':repr(e)}
  tb=tb.tb_next
 (p/'failure-state.json').write_text(json.dumps(state,indent=2)+'\n');raise
for rec in previous['fixtures']:assert sha(out/Path(rec['module']).name)==rec['sha256']
proof['status']='PASS completed prefix verified; all later checks passed';(p/'prefix-reuse.json').write_text(json.dumps(proof,indent=2)+'\n')
