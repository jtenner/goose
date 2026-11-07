from pathlib import Path
import hashlib,json,tempfile
p=Path(__file__).parent;source=Path('/home/dev/Projects/goose-wasm-backend/test/wasm_data_aggregate_named.py');old=source.read_text();assert old.count('p.mkdir();')==1;new=old.replace('p.mkdir();','p.mkdir(exist_ok=True);');(p/'helper-before.py').write_text(old);(p/'helper-fixed.py').write_text(new)
class ReachedEmit(Exception):pass
rows=[]
for name,text in [('before',old),('fixed',new)]:
 ns={'__file__':str(source)};exec(compile(text,str(source),'exec'),ns)
 for existing in [False,True]:
  with tempfile.TemporaryDirectory(dir=p) as tmp:
   out=Path(tmp);target=out/'data-named-copy'
   if existing:target.mkdir()
   calls=[]
   def command(args):calls.append(args);raise ReachedEmit()
   try:ns['check_named_footprint'](command,'no-compiler','no-cc','no-node','no-validator',None,out,None)
   except ReachedEmit:result='emitter reached'
   except FileExistsError:result='FileExistsError'
   expected='FileExistsError' if name=='before' and existing else 'emitter reached';assert result==expected,(name,existing,result);assert len(calls)==(0 if result=='FileExistsError' else 1)
   rows.append({'version':name,'existing_output':existing,'observed':result,'compiler_or_guest_executed':False})
v={'before_sha256':hashlib.sha256(old.encode()).hexdigest(),'fixed_sha256':hashlib.sha256(new.encode()).hexdigest(),'cases':rows,'result':'PASS: actual old helper rejects reused output before emitter; one directory option repairs it, with fresh output also retained.'};(p/'harness-reuse-results.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
