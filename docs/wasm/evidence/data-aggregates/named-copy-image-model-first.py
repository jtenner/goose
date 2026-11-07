from pathlib import Path
import hashlib,json
b=Path(__file__).parent;rows=[]
def initial_image(data,length):
 def leb(pos,signed=False):
  v=s=0
  while True:
   q=data[pos];pos+=1;v|=(q&127)<<s;s+=7
   if not q&128:
    if signed and q&64:v-=1<<s
    return v,pos
 p=8;globals_=[];image=bytearray(length);segments=[]
 while p<len(data):
  tag=data[p];size,c=leb(p+1);end=c+size
  if tag==6:
   n,c=leb(c)
   for _ in range(n):
    assert data[c:c+3]==b'\x7f\x01\x41';v,c=leb(c+3,True);assert data[c]==11;c+=1;globals_.append(v)
   assert c==end
  if tag==11:
   n,c=leb(c)
   for _ in range(n):
    flags,c=leb(c);assert flags==0;assert data[c]==0x41;offset,c=leb(c+1,True);assert data[c]==11;c+=1;size,c=leb(c);payload=data[c:c+size];c+=size;image[offset:offset+size]=payload;segments.append({'offset':offset,'payload':payload})
   assert c==end
  p=end
 assert globals_ and len(segments)==1 and segments[0]['offset']==0
 return image,globals_[0],segments[0]['payload']
for phase,unit,sub in [('before','named-copy-before01',''),('after','build06','data-named-copy')]:
 p=b/unit/sub;records=json.loads((p/'results.json').read_text())
 for entry in records:
  stem=f"{entry['kind']}-{entry['binding']}-{entry['base']}-{entry['amount']}";name=stem+f"-O{entry['opt']}";module=p/(name+'.wasm');assert hashlib.sha256(module.read_bytes()).hexdigest()==entry['module_sha256'];capture=p/(name+'-instance');actual=(capture/'memory.bin').read_bytes();model,frame_start,static=initial_image(module.read_bytes(),len(actual));source=p/(stem+'.goose');assert hashlib.sha256(source.read_bytes()).hexdigest()==entry['source_sha256']
  prefix=12 if entry['binding']=='global' else 8;assert static[:prefix]==bytes(prefix);tail=static[prefix:];path=str(source).encode();assert tail.replace(path,b'')==b'named-copy=ok',(phase,name,'static bytes other than filename diagnostics/output literal')
  address=8 if entry['binding']=='global' else frame_start;model[address:address+4]=bytes([7,0,9,0]);assert actual==model,(phase,name,'complete Memory0 model')
  rows.append({'phase':phase,'name':name,'memory0_sha256':hashlib.sha256(actual).hexdigest(),'static_bytes':len(static),'filename_copies':tail.count(path),'frame_start':frame_start,'template_address':address,'full_model':'PASS'})
before=json.loads((b/'named-copy-before01/results.json').read_text());after=json.loads((b/'build06/data-named-copy/results.json').read_text());pairs=0
for a,c in zip(before,after):
 stem=f"{a['kind']}-{a['binding']}-{a['base']}-{a['amount']}-O{a['opt']}-instance"
 for image in (b/'named-copy-before01'/stem).glob('data_memory_*.bin'):
  assert image.read_bytes()==(b/'build06/data-named-copy'/stem/image.name).read_bytes(),(stem,image.name);pairs+=1
result={'status':'PASS','complete_memory0_models':len(rows),'exact_complete_data_image_pairs':pairs,'guest_or_compiler_runs':0,'scope':'Saved byte parsing only. Memory0 static bytes must be zero prefix + exact source filename repetitions + exact output literal; only template bytes at declared global/frame start may differ from initial data. Data memories byte-identical and independently modeled by retained runs.','cases':rows};(b/'named-copy-image-model.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='cases'}))
