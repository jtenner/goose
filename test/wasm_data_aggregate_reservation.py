"""Wasmtime counterpart of the pre-child reservation controls."""
from pathlib import Path
import json,sys,wasmtime
path,mode,result_path=sys.argv[1:4];expected_line=int(sys.argv[4]) if len(sys.argv)>4 else None;config=wasmtime.Config();config.wasm_multi_memory=True;config.wasm_exceptions=True
engine=wasmtime.Engine(config);module=wasmtime.Module.from_file(engine,path);store=wasmtime.Store(engine);linker=wasmtime.Linker(engine)
pending={};output=[];observed=False;before=None;serial=0
class Failure(Exception):pass

def exports(caller):return {n:x[n] for n in names}
def tops(caller):return [(n,x[n].value(caller)) for n in names if n.startswith('test_stack_top_')]
def images(caller):return {n:bytes(x[n].read(caller)) for n in names if n=='memory' or n.startswith('data_memory_')}
def dispatch(name,caller,args):
 global serial,observed,before
 if name=='print_begin_v1':serial+=1;pending[serial]=[];return serial
 if name=='print_bytes_v1':pending[args[0]].append(bytes(caller.get('memory').read(caller,args[1]&0xffffffff,(args[1]&0xffffffff)+(args[2]&0xffffffff))));return
 if name=='print_end_v1':
  line=b''.join(pending.pop(args[0]))+b'\n';output.append(line)
  if line!=b'ready\n':return
  assert not observed;observed=True;x=exports(caller);assert x['test_stack_top_1'].value(caller)==1
  if mode.startswith('growth'):x['data_memory_1'].write(caller,bytes([0xaa])*x['data_memory_1'].data_len(caller))
  if mode=='overflow':
   source=x['data_memory_2'];assert bytes(source.read(caller,1,9))==bytes([1,0,0,0,11,0,0,0]);source.write(caller,(0xffffffff).to_bytes(4,'little'),1)
  before={'tops':tops(caller),'memories':images(caller)};return
 if name=='fail_v1':raise Failure(args[0],args[3])
 raise AssertionError('unexpected import '+name)
for imported in module.imports:
 assert imported.module=='goose' and isinstance(imported.type,wasmtime.FuncType)
 def callback(caller,*args,name=imported.name):return dispatch(name,caller,args)
 linker.define_func('goose',imported.name,imported.type,callback,access_caller=True)
instance=linker.instantiate(store,module);x=instance.exports(store);names=[e.name for e in module.exports]
failure=mode in ('overflow','growth-failure','growth-bad-zero')
if failure:
 try:x['_start'](store)
 except Failure as error:
  if mode=='growth-bad-zero':assert error.args==(1,expected_line),error.args
  else:assert error.args[0]==6,error.args
 else:raise AssertionError('expected reservation failure')
 if mode=='growth-bad-zero':assert x['data_memory_1'].read(store,40005,40006)==bytearray([0xaa])
 else:
  assert b''.join(output)==b'ready\n';assert tops(store)==before['tops'];assert images(store)==before['memories']
else:
 x['_start'](store);assert b''.join(output)==b'ready\nchild\nchild\ndone\n'
 image=bytes(x['data_memory_1'].read(store));model=bytearray(len(image));model[0]=0xaa;model[1:5]=(2).to_bytes(4,'little');model[5]=3;model[40006]=3;assert image==model
 assert all(value==1 for name,value in tops(store) if name!='test_stack_top_0')
assert observed and not pending
Path(result_path).write_text(json.dumps({'mode':mode,'observedReady':observed,'expectedFailure':failure,'tops':tops(store),'allChecks':'PASS'},indent=2)+'\n')
sys.stdout.buffer.write(b'allocation-control=ok\n' if failure else b''.join(output))
