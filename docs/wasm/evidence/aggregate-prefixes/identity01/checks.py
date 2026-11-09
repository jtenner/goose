from pathlib import Path
import json,hashlib,subprocess,re,sys
p=Path(__file__).parent;raw=p.parent;r=Path('/home/dev/Projects/goose-wasm-backend')
partial='--preload' in sys.argv
if not partial:
 assert (raw/'full-correctness07/check.exit').read_text().strip()=='0'
 proof=json.loads((raw/'full-correctness07/prefix-reuse.json').read_text());assert proof['status']=='PASS completed prefix verified; all later checks passed'
old=Path('/tmp/goose-wasm-array-prefix-conversion-20261108');parent=old/'full-correctness01/artifacts';current=raw/('full-correctness03/artifacts' if partial else 'full-correctness07/artifacts');oldhash=json.loads((old/'validation-inputs.json').read_text());rows=[];changes=[]
for source in sorted((r/'test/wasm').glob('*.goose')):
 for opt in [0,2]:
  name=source.stem+f'-O{opt}.wasm';before=parent/name
  if not before.exists():continue
  assert hashlib.sha256(source.read_bytes()).hexdigest()==oldhash[str(source.relative_to(r))]
  after=current/name
  if partial and not after.exists():continue
  assert after.exists(),name
  row={'source':str(source.relative_to(r)),'opt':opt,'parent':str(before),'parent_sha256':hashlib.sha256(before.read_bytes()).hexdigest(),'sha256':hashlib.sha256(after.read_bytes()).hexdigest()}
  if before.read_bytes()==after.read_bytes():row['status']='identical'
  else:
   texts=[]
   for label,f in [('parent',before),('candidate',after)]:
    cache=p/(name+'.'+label+'.wat');stamp=p/(name+'.'+label+'.sha256.txt')
    digest=hashlib.sha256(f.read_bytes()).hexdigest()
    if cache.exists() and stamp.exists() and stamp.read_text().strip()==digest:text=cache.read_text()
    else:
     a=subprocess.run(['wasm-tools','print',f],capture_output=True);assert a.returncode==0,a.stderr
     text=a.stdout.decode();cache.write_text(text);stamp.write_text(digest+'\n')
    texts.append(text)
   def clears(t):return len(re.findall(r'\bmemory.fill\b|call \$goose.fill_memory\b',t))
   assert clears(texts[1])>clears(texts[0]),(name,clears(texts[0]),clears(texts[1]))
   row.update(status='fresh-unused-slot-clear',parent_clear_sites=clears(texts[0]),candidate_clear_sites=clears(texts[1]));changes.append(name)
  rows.append(row)
if not partial:assert len(rows)==1592,len(rows)
(p/('partial-results.json' if partial else 'results.json')).write_text(json.dumps(rows,indent=2)+'\n')
(p/('partial-changed-modules.json' if partial else 'changed-modules.json')).write_text(json.dumps(changes,indent=2)+'\n')
print('PRELIMINARY' if partial else 'PASS',len(rows),'parent fixture modules;',len(rows)-len(changes),'identical,',len(changes),'gain explicit unused-slot clear sites')
