"""Reuse the observed completed fixture prefix, execute every later check."""
from pathlib import Path
import ast,copy,hashlib,json,shutil,sys,importlib.util
p=Path(__file__).parent;raw=p.parent;r=Path('/home/dev/Projects/goose-wasm-backend');previous=raw/'full-correctness03';out=p/'artifacts';out.mkdir(exist_ok=True)
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
assert (previous/'check.exit').read_text().strip()=='1'
error=(previous/'check.stderr').read_text()
assert 'line 444, in main' in error and 'count += check_aggregate_construction(' in error and 'aggregate fill complete Memory 0 image differs' in error
original=json.loads((previous/'validation-inputs.json').read_text());current=json.loads((raw/'validation-inputs.json').read_text())
changed=[n for n,h in original.items() if current[n]!=h]
assert set(changed)=={'test/wasm_aggregate_construction_image.mjs','test/wasm_aggregate_construction_checks.py'},changed
for n,h in current.items():assert sha(r/n)==h,n
for n,h in json.loads((raw/'build02/source-hashes.json').read_text()).items():assert sha(r/n)==h,n
identity=json.loads((raw/'compiler-identity.json').read_text());assert sha(raw/'build02/goose-tested')==identity['sha256']
fixtures=sorted((r/'test/wasm').glob('*.goose'))+[r/'test/typing'/(n+'.goose') for n in ['global_optional_flow','optional_loop_callee_assignments','optional_while_condition_calls','u64_cmp_readonly_refs']]
rows=[]
for source in fixtures:
 assert sha(source)==original[str(source.relative_to(r))]
 for opt in (0,2):
  name=source.stem+f'-O{opt}';module=previous/'artifacts'/(name+'.wasm')
  assert module.read_bytes()[:8]==b'\0asm\x01\0\0\0'
  assert (previous/'artifacts'/(name+'.c')).is_file() and (previous/'artifacts'/(name+'.native')).is_file()
  rows.append({'source':str(source.relative_to(r)),'opt':opt,'sha256':sha(module)})
  shutil.copy2(module,out/module.name)
# Core module tests also returned before the observed failing helper.
for name in ['memory-runtime.wasm','memory-runtime-limited.wasm','memory-copy-matrix.wasm','array-places.wasm']:
 shutil.copy2(previous/'artifacts'/name,out/name)
sys.path.insert(0,str(r/'test'))
spec=importlib.util.spec_from_file_location('wasm_backend',r/'test/wasm_backend.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
tree=ast.parse((r/'test/wasm_backend.py').read_text());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
start=next(i for i,n in enumerate(main.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='count' for t in n.targets))
loop=next(i for i,n in enumerate(main.body) if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='source')
def count_only(n):
 if isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and n.target.id=='count':return copy.deepcopy(n)
 if isinstance(n,(ast.If,ast.For)):
  body=[v for child in n.body if (v:=count_only(child)) is not None];other=[v for child in n.orelse if (v:=count_only(child)) is not None]
  if not body and not other:return None
  result=copy.deepcopy(n);result.body=body or [ast.Pass()];result.orelse=other;return result
 return None
# These count operations describe checks already completed in full-correctness03.
# The failure point is after the whole fixture loop. They do not execute guests.
reused=[]
for n in main.body[start+1:loop+1]:
 if isinstance(n,ast.Assign) and not any(isinstance(v,ast.Call) and isinstance(v.func,ast.Name) and v.func.id=='run' for v in ast.walk(n)):reused.append(copy.deepcopy(n))
 elif isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and isinstance(n.value.func.value,ast.Name) and n.value.func.value.id=='sources':reused.append(copy.deepcopy(n))
 v=count_only(n)
 if v is not None:reused.append(v)
# Require that the counting-only loop has no dependency on omitted execution values.
loads={n.id for item in reused for n in ast.walk(item) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Load)}
assert loads<= {'out','args','ROOT','sorted','sources','source','opt','count','name'},loads
proof={'status':'PASS prefix reuse only; continuation not yet run','basis':'full-correctness03 reached line444 after all fixture and core-unit assertions; later observer failed','source_compiler_sha256':identity['sha256'],'changed_helpers':changed,'fixture_pairs':len(rows),'fixtures':rows}
def record_prefix(scope):
 proof['completed_core_and_fixture_checks']=scope['count'];proof['later_checks']='executed afresh by the unmodified suffix of wasm_backend.main'
 (p/'prefix-reuse.json').write_text(json.dumps(proof,indent=2)+'\n')
 print('Reused',scope['count'],'completed core/fixture checks after hashes and observed control-flow verification',flush=True)
main.body=copy.deepcopy(main.body[:start+1])+reused+[ast.Expr(ast.Call(ast.Name('record_prefix',ast.Load()),[ast.Call(ast.Name('locals',ast.Load()),[],[])],[]))]+copy.deepcopy(main.body[loop+1:])
m.record_prefix=record_prefix;compiled=ast.fix_missing_locations(ast.Module([main],type_ignores=[]));exec(compile(compiled,str(r/'test/wasm_backend.py'),'exec'),m.__dict__)
sys.argv=[str(r/'test/wasm_backend.py'),*sys.argv[1:]];m.main()
assert all(sha(out/(Path(x['source']).stem+f"-O{x['opt']}.wasm"))==x['sha256'] for x in rows)
proof['status']='PASS completed prefix verified; all later checks passed';(p/'prefix-reuse.json').write_text(json.dumps(proof,indent=2)+'\n')
