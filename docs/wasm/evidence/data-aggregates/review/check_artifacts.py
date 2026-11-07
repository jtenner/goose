from pathlib import Path
import json,hashlib,collections
P=Path('/tmp/goose-wasm-data-aggregates-review-20261107');R=Path('/tmp/goose-wasm-data-aggregates-20261107');W=Path('/home/dev/Projects/goose-wasm-backend');O=P/'review';reads=[]
def data(f,mode='hash/byte comparison'):
 f=Path(f);reads.append({'path':str(f),'mode':mode});return f.read_bytes()
def sha(b):return hashlib.sha256(b).hexdigest()
def j(f):return json.loads(data(f,'parsed JSON content'))
def metric(f):
 b=data(f,'parsed Wasm sections and local declarations, not instruction semantics');p=8;counts=[];codebytes=0
 assert b[:8]==b'\0asm\1\0\0\0'
 def u():
  nonlocal p
  v=s=0
  while True:
   x=b[p];p+=1;v|=(x&127)<<s
   if x<128:return v
   s+=7
 while p<len(b):
  tag=b[p];p+=1;size=u();end=p+size
  if tag==10:
   codebytes=size
   for _ in range(u()):
    size=u();bodyend=p+size;n=0
    for _ in range(u()):n+=u();assert b[p] in (0x7f,0x7e,0x7d,0x7c);p+=1
    assert p<bodyend and b[bodyend-1]==11;counts.append(n);p=bodyend
   assert p==end
  p=end
 assert p==len(b)
 return {'module_bytes':len(b),'code_section_bytes':codebytes,'functions':len(counts),'local_count':sum(counts),'max_function_locals':max(counts,default=0)},counts,sha(b)
result={'scaling':[],'images':[],'reuse':[],'compatibility':[],'warning_comments':[]}
for unit in ['scaling-before01','scaling-after01','unknown-scaling-before01','unknown-scaling-after01']:
 for row in j(R/unit/'results.json'):
  kind=row.get('kind','unknown');n=row['amount'];stem=f'{kind}-{n}'+(f"-O{row['opt']}" if 'opt' in row else '')
  m,loc,h=metric(R/unit/(stem+'.wasm'));assert loc==row['local_counts'] and h==row['module_sha256'] and m['module_bytes']==row['module_bytes']
  result['scaling'].append({'unit':unit,'stem':stem,**m})
  inst=R/unit/(stem+'-instance');state=j(inst/'instance.json');assert state['completionCalls']==1 and state['pendingPrints']==state['pendingSnapshots']==0
  for e in state['memories']:
   b=data(inst/(e['name']+'.bin'),'full memory byte model/comparison');assert len(b)==e['bytes'] and sha(b)==e['sha256']
   if e['name']=='memory':continue
   image=bytes([1,7,0,7,0,97,98,99])+bytes(8)+bytes([2]) if kind=='fill-and-text' else bytes([1,2,7,0,8,0,0,0,2])
   model=bytearray(bytes(1)+n.to_bytes(4,'little')+image*n);model+=bytes(len(b)-len(model))
   if kind=='unknown' and e['name']=='data_memory_1':model[1:5]=(1).to_bytes(4,'little');model[5:13]=(91).to_bytes(8,'little')
   assert b==model,(unit,stem,e['name']);result['images'].append(str(inst/(e['name']+'.bin')))
  if '-after' in unit:
   before=R/unit.replace('-after','-before')/(stem+'-instance')
   for e in state['memories']:assert data(inst/(e['name']+'.bin'))==data(before/(e['name']+'.bin'))
for row in j(R/'build05/candidate-results.json'):
 stem=f"candidate-{row['family']}-O{row['opt']}";_,_,h=metric(R/'build05'/(stem+'.wasm'));assert h==row['module_sha256']
 a=R/'build04'/(stem+'-instance');b=R/'build05'/(stem+'-instance');sa=j(a/'instance.json');sb=j(b/'instance.json');assert sa==sb and sb['completionCalls']==1 and sb['pendingPrints']==sb['pendingSnapshots']==0
 for e in sb['memories']:
  x=data(b/(e['name']+'.bin'),'full memory byte comparison');assert sha(x)==e['sha256'] and x==data(a/(e['name']+'.bin'));result['images'].append(str(b/(e['name']+'.bin')))
for unit,name in [('scaling-after01','verified-native-reuse.json'),('unknown-scaling-after01','verified-native-reuse.json'),('build03','verified-parent-reuse.json'),('build04','verified-parent-reuse.json'),('build05','verified-helper-reuse.json')]:
 row=j(R/unit/name);root=Path(row['source'])
 for f,h in row['files'].items():assert sha(data(root/f))==h,(unit,f)
 result['reuse'].append({'unit':unit,'files':len(row['files']),'source':str(root)})
rows=j(R/'compatibility02/module-deltas.json');meta=j(R/'compatibility02/module-metadata.json');parent=j(R/'compatibility02/parent-module-manifest.json');assert len(rows)==len(parent)==234
for e,record,pm in zip(rows,meta['rows'],parent):
 assert all(e[k]==v for k,v in pm.items());assert sha(data(W/e['source']))==e['source_sha256'];a,_,ah=metric(e['parent_module']);b,_,bh=metric(e['candidate_module']);assert ah==e['parent_sha256'] and bh==e['candidate_sha256'];assert a==record['parent'] and b==record['candidate'];assert e['identical']==(ah==bh);assert b['module_bytes']-a['module_bytes']==e['delta_bytes'];result['compatibility'].append({'source':e['source'],'opt':e['opt'],'identical':e['identical'],'delta':{k:b[k]-a[k] for k in a}})
result['compatibility_summary']={'pairs':len(rows),'identical':sum(x['identical'] for x in rows),'total_deltas':{k:sum(x['delta'][k] for x in result['compatibility']) for k in a}}
assert result['compatibility_summary']['total_deltas']==meta['summary']['total_deltas']
for e in j(R/'compatibility02/warning-marker-provenance.json'):
 before=data(R/'native-baseline01/failed-warning-fixtures'/Path(e['source']).name,'exact removed-comment source comparison');now=data(W/e['source']);prefix=''.join('// warning: '+m+'\n' for m in e['added_comment_lines']).encode();assert now==prefix+before and sha(before)==e['before'] and sha(now)==e['after'];result['warning_comments'].append(e['source'])
(O/'artifact-checks.json').write_text(json.dumps(result,indent=2)+'\n');(O/'artifact-read-log.json').write_text(json.dumps(reads,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['compatibility','images']},indent=2));print('checked images',len(result['images']))
