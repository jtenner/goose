from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;raw=p.parent;r=Path('/home/dev/Projects/goose-wasm-backend');identity=json.loads((raw/'parent-compiler-identity.json').read_text());exe=Path(identity['compiler']);rows=[];i=0
assert hashlib.sha256(exe.read_bytes()).hexdigest()==identity['sha256']
def run(args):
 global i
 i+=1;args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120)
 (p/f'command-{i:04}.json').write_text(json.dumps(args)+'\n')
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/f'command-{i:04}.{k}').write_bytes(v)
 return a,i
manifest=json.loads((raw/'prepared-families.json').read_text());byname={x['case']:x for x in manifest}
for previous in json.loads((raw/'parent02/results.json').read_text()):
 name=previous['case'];record=byname[name];source=raw/'prepared'/(name+'.goose')
 assert previous['source_sha256']==record['source_sha256']==hashlib.sha256(source.read_bytes()).hexdigest()
 for label,index in previous['commands'].items():
  producer=raw/'parent02'/f'command-{index:04}'
  status=int(producer.with_suffix('.exit').read_text());assert status==(1 if label=='wasm' and previous['kind']!='parent-supported' else 0),(name,label,status)
  args=json.loads(producer.with_suffix('.json').read_text())
  if label in ['emit','wasm']:assert args[0]==str(exe) and args[-1]==str(source)
  if label=='native':assert producer.with_suffix('.stdout').read_bytes()==record['expected'].encode() and not producer.with_suffix('.stderr').read_bytes()
 rows.append(dict(previous,producer_phase='parent02'))
reused={x['case'] for x in rows}
for record in manifest:
 if record['case'] in reused:continue
 name=record['case'];source=raw/'prepared'/(name+'.goose');assert hashlib.sha256(source.read_bytes()).hexdigest()==record['source_sha256'],name
 c=p/(name+'.c');native=p/(name+'.native');module=p/(name+'.wasm');commands={}
 for label,args in [('emit',[exe,'-O0','--standalone','-o',c,source]),('cc',['cc','-O0',c,'-pthread','-lm','-ldl','-o',native]),('native',[native]),('wasm',[exe,'-O0','--target','wasm','-o',module,source])]:
  a,index=run(args);commands[label]=index
  if label!='wasm':
   assert a.returncode==0,(name,label,a.returncode,a.stderr)
   if label=='native':assert a.stdout==record['expected'].encode() and not a.stderr,(name,a.stdout,a.stderr)
  elif a.returncode==0:
   b,_=run(['wasm-tools','validate',module]);assert not b.returncode,b.stderr
   b,_=run(['node',r/'scripts/run_wasm.mjs',module]);assert not b.returncode and b.stdout==record['expected'].encode() and not b.stderr,(name,b.returncode,b.stderr)
   kind='parent-supported'
  else:
   assert a.returncode==1 and not module.exists(),(name,a.returncode,a.stderr)
   if b'array adaptation needs the pending destination lowering' in a.stderr:kind='missing-conversion'
   elif name=='grow_indexed_reference' and b'compound array elements need the pending layout lowering' in a.stderr:kind='retained-compound-guard'
   else:kind='other-parent-rejection'
 rows.append({'producer_phase':'parent03','case':name,'source_sha256':record['source_sha256'],'kind':kind,'commands':commands,'status':'native PASS; parent Wasm classified'})
 (p/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print('PASS reused',len(reused),'and total',len(rows),'native-valid cases; parent Wasm classes',json.dumps({k:sum(x['kind']==k for x in rows) for k in sorted({x['kind'] for x in rows})}))
