from pathlib import Path
import json,hashlib,subprocess,re
p=Path(__file__).parent;raw=p.parent;r=Path('/home/dev/Projects/goose-wasm-backend')
assert (raw/'full-correctness02/check.exit').read_text().strip()=='0'
old=Path('/tmp/goose-wasm-array-prefix-conversion-20261108');parent=old/'full-correctness01/artifacts';current=raw/'full-correctness02/artifacts';oldhash=json.loads((old/'validation-inputs.json').read_text());rows=[];changes=[]
for source in sorted((r/'test/wasm').glob('*.goose')):
 for opt in [0,2]:
  name=source.stem+f'-O{opt}.wasm';before=parent/name
  if not before.exists():continue
  assert hashlib.sha256(source.read_bytes()).hexdigest()==oldhash[str(source.relative_to(r))]
  after=current/name;assert after.exists(),name
  row={'source':str(source.relative_to(r)),'opt':opt,'parent':str(before),'parent_sha256':hashlib.sha256(before.read_bytes()).hexdigest(),'sha256':hashlib.sha256(after.read_bytes()).hexdigest()}
  if before.read_bytes()==after.read_bytes():row['status']='identical'
  else:
   texts=[]
   for label,f in [('parent',before),('candidate',after)]:
    a=subprocess.run(['wasm-tools','print',f],capture_output=True);assert a.returncode==0,a.stderr
    text=a.stdout.decode();(p/(name+'.'+label+'.wat')).write_text(text);texts.append(text)
   def clears(t):return len(re.findall(r'\bmemory.fill\b|call \$goose.fill_memory\b',t))
   assert clears(texts[1])>clears(texts[0]),(name,clears(texts[0]),clears(texts[1]))
   row.update(status='fresh-unused-slot-clear',parent_clear_sites=clears(texts[0]),candidate_clear_sites=clears(texts[1]));changes.append(name)
  rows.append(row)
assert len(rows)==1592,len(rows)
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
(p/'changed-modules.json').write_text(json.dumps(changes,indent=2)+'\n')
print('PASS',len(rows),'parent fixture modules;',len(rows)-len(changes),'identical,',len(changes),'gain explicit unused-slot clear sites')
