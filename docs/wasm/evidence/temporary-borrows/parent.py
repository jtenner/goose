from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');out=p/'parent01';out.mkdir(exist_ok=True);exe=Path('/tmp/goose-wasm-fixed-lifetime-plan-20261109/build03/goose-tested');rows=[];serial=0
for x in json.loads((p/'families.json').read_text()):
 f=Path(x['source']);pair=[]
 for opt in (0,2):
  prefix=out/(x['case']+f'-O{opt}');c,native,module=[prefix.with_suffix(e) for e in ['.c','.native','.wasm']]
  for label,args in [('native-emit',[exe,f'-O{opt}','--standalone','-o',c,f]),('native-build',['cc',f'-O{opt}',c,'-pthread','-lm','-ldl','-o',native]),('native-run',[native]),('wasm-emit',[exe,f'-O{opt}','--target','wasm','-o',module,f])]:
   serial+=1;args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120);base=out/f'command-{serial:04}'
   base.with_suffix('.json').write_text(json.dumps(args)+'\n');base.with_suffix('.stdout').write_bytes(a.stdout);base.with_suffix('.stderr').write_bytes(a.stderr);base.with_suffix('.exit').write_text(str(a.returncode)+'\n')
   if label=='native-emit' and a.returncode:
    pair.append({'case':x['case'],'opt':opt,'status':'invalid source sketch','stderr':a.stderr.decode()});break
   if label=='wasm-emit':
    pair.append({'case':x['case'],'opt':opt,'status':'native-valid Wasm failure' if a.returncode else 'supported parent regression','stderr':a.stderr.decode(),'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'source':str(f),'expected':x['expected']});break
   assert not a.returncode,(x['case'],opt,label,a.stderr)
   if label=='native-run':assert a.stdout==x['expected'].encode() and not a.stderr,(x['case'],opt,a.stdout,a.stderr)
  if pair and pair[-1]['status']=='invalid source sketch':break
 rows+=pair;(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
valid=[]
for x in json.loads((p/'families.json').read_text()):
 rs=[v for v in rows if v['case']==x['case']]
 if len(rs)==2 and all(v['status']!='invalid source sketch' for v in rs):valid.append(x)
(p/'valid-families.json').write_text(json.dumps(valid,indent=2)+'\n');print('PASS',len(valid),'native-valid families,',sum(v['status']=='native-valid Wasm failure' for v in rows),'parent target failures');print('invalid',[(v['case'],v['stderr']) for v in rows if v['status']=='invalid source sketch'])
