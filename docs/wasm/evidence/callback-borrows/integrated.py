"""Run fresh core/suffix checks; verify and reuse executed fixture pairs."""
from pathlib import Path
import ast,copy,hashlib,json,shutil,sys,importlib.util
raw=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');p=raw/'full-correctness01';p.mkdir(exist_ok=True);out=p/'artifacts';out.mkdir(exist_ok=True)
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
inputs=json.loads((raw/'validation-inputs.json').read_text());sources=json.loads((raw/'build03/source-hashes.json').read_text())
for n,h in {**inputs,**sources}.items():assert sha(r/n)==h,n
identity=json.loads((raw/'compiler-identity.json').read_text());assert sha(identity['compiler'])==identity['sha256']
old=Path('/tmp/goose-wasm-temporary-borrows-20261109');oldinputs=json.loads((old/'validation-inputs.json').read_text())
assert {n for n,h in oldinputs.items() if inputs.get(n)!=h}=={'test/wasm_backend.py'}
assert len(set(inputs)-set(oldinputs))==46
assert (old/'full-correctness01/check.exit').read_text().strip()=='0'
assert (raw/'identity01/check.exit').read_text().strip()=='0'
oldrows=json.loads((raw/'identity01/results.json').read_text());assert len(oldrows)==2094
records={}
for x in oldrows:
 assert x['sha256']==x['parent_sha256'];source=r/x['source'];assert sha(source)==oldinputs[x['source']]==x['source_sha256']
 module=raw/'identity01'/(source.stem+f"-O{x['opt']}.wasm");assert sha(module)==x['sha256']
 records[x['source'],x['opt']]={'source':x['source'],'opt':x['opt'],'sha256':x['sha256'],'module':str(module),'basis':'executed parent fixture and byte-identical candidate'}
assert (raw/'focused01/check.exit').read_text().strip()=='0'
for x in json.loads((raw/'focused01/results.json').read_text()):
 source='test/wasm/'+x['case']+'.goose';assert sha(r/source)==x['source_sha256']==inputs[source];assert x['status']=='PASS';module=raw/'focused01'/(x['case']+f"-O{x['opt']}.wasm");assert sha(module)==x['wasm_sha256'];assert (source,x['opt']) not in records
 records[source,x['opt']]={'source':source,'opt':x['opt'],'sha256':x['wasm_sha256'],'module':str(module),'basis':'fresh native/Node/Wasmtime positive callback borrowed-temporary fixture'}
fixtures=sorted((r/'test/wasm').glob('*.goose'))+[r/'test/typing'/(n+'.goose') for n in ['global_optional_flow','optional_loop_callee_assignments','optional_while_condition_calls','u64_cmp_readonly_refs']]
assert {(str(f.relative_to(r)),o) for f in fixtures for o in (0,2)}==set(records);assert len(records)==2138
for rec in records.values():shutil.copy2(rec['module'],out/Path(rec['module']).name)
sys.path.insert(0,str(r/'test'));spec=importlib.util.spec_from_file_location('wasm_backend',r/'test/wasm_backend.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
tree=ast.parse((r/'test/wasm_backend.py').read_text());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');loop=next(i for i,n in enumerate(main.body) if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='source')
def count_only(n):
 if isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and n.target.id=='count':return copy.deepcopy(n)
 if isinstance(n,(ast.If,ast.For)):
  body=[v for c in n.body if (v:=count_only(c)) is not None];other=[v for c in n.orelse if (v:=count_only(c)) is not None]
  if not body and not other:return None
  a=copy.deepcopy(n);a.body=body or [ast.Pass()];a.orelse=other;return a
 return None
reused=count_only(main.body[loop]);loads={n.id for n in ast.walk(reused) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Load)};assert loads<={'sources','source','opt','count','args'},loads
proof={'status':'fixture hashes PASS; fresh core and suffix not complete','compiler_sha256':identity['sha256'],'fixture_pairs':len(records),'old_byte_identical_pairs':2094,'new_executed_pairs':44,'fixtures':list(records.values())}
def record(scope):
 proof['fresh_core_and_reused_fixture_checks']=scope['count'];(p/'fixture-reuse.json').write_text(json.dumps(proof,indent=2)+'\n');print('Verified and reused',len(records),'fixture pairs; core and all suffix checks run fresh',flush=True)
main.body=main.body[:loop]+[reused,ast.Expr(ast.Call(ast.Name('record_fixture_reuse',ast.Load()),[ast.Call(ast.Name('locals',ast.Load()),[],[])],[]))]+main.body[loop+1:]
m.record_fixture_reuse=record;exec(compile(ast.fix_missing_locations(ast.Module([main],type_ignores=[])),str(r/'test/wasm_backend.py'),'exec'),m.__dict__);sys.argv=[str(r/'test/wasm_backend.py'),*sys.argv[1:]]
try:m.main()
except BaseException as error:
 tb=error.__traceback__;state={}
 while tb:
  if tb.tb_frame.f_code.co_name=='main':state={'completed_checks':tb.tb_frame.f_locals.get('count'),'line':tb.tb_lineno,'exception':repr(error)}
  tb=tb.tb_next
 (p/'failure-state.json').write_text(json.dumps(state,indent=2)+'\n');raise
for rec in records.values():assert sha(out/Path(rec['module']).name)==rec['sha256']
proof['status']='PASS verified fixture reuse; fresh core and all suffix checks passed';(p/'fixture-reuse.json').write_text(json.dumps(proof,indent=2)+'\n')
