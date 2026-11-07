from pathlib import Path
import re,json
p=Path(__file__).parent
rows=json.loads((p/'classification.json').read_text())
def normalize(text,after):
 pattern=r'^  \(func \$goose\.copy_(?:memory|to_frame)\b.*?^  \)\n'
 assert len(re.findall(pattern,text,re.M|re.S))==1
 text=re.sub(pattern,'',text,flags=re.M|re.S)
 casts=0
 if after:
  text,casts=re.subn(r'(local\.get \d+)\s+i32\.wrap_i64\s+(local\.get \d+)\s+(local\.get \d+)\s+call \$goose\.copy_to_frame',lambda m:'\n'.join([m[1],m[2],m[3],'call $goose.copy_memory']),text)
 text=re.sub(r'^  \(type .*\n','',text,flags=re.M)
 text=re.sub(r'\(;\d+;\)','',text)
 text=re.sub(r'\(type \d+\)','',text)
 return [' '.join(line.split()) for line in text.splitlines() if line.strip()],casts
for row in rows:
 stem=Path(row['source']).stem+'-O'+str(row['opt'])
 a=(p/(stem+'-before.stdout')).read_text();b=(p/(stem+'-after.stdout')).read_text()
 before,_=normalize(a,False);after,casts=normalize(b,True)
 assert before==after and casts==row['converted_calls'],stem
 ta={re.sub(r'\(;\d+;\)','',line).strip() for line in a.splitlines() if line.startswith('  (type ')}
 tb={re.sub(r'\(;\d+;\)','',line).strip() for line in b.splitlines() if line.startswith('  (type ')}
 assert ta-tb=={'(type  (func (param i64 i64 i32)))'} and not tb-ta
print(str(len(rows))+' helper-only classifications verified from saved dumps')
