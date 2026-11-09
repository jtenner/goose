import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate, GooseFailure } from '../scripts/run_wasm.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const [file,mode]=process.argv.slice(2);assert(mode==='product'||mode==='sum');
const value=mode==='product'?3353953467947191203n:390451572n;
if(mode==='product')assert.equal(BigInt.asUintN(64,value*11n),1n);
let runtime,initial,frame,images=[],seen=0;
runtime=instantiate(fs.readFileSync(file),bytes=>{
    const label=Buffer.from(bytes).toString('utf8').trim(),e=runtime.instance.exports;
    assert.equal(label,'before','LEB corrupted count reached copy');assert.equal(seen++,0);
    assert.equal(e.test_stack_top_0.value,initial);assert.equal(e.test_stack_top_1.value,1411);
    for(let i=2;i<=3;i++){assert.equal(e[`test_stack_top_${i}`].value,1);if(!e[`data_memory_${i}`].buffer.byteLength)e[`data_memory_${i}`].grow(1);new Uint8Array(e[`data_memory_${i}`].buffer).fill(165,1);}
    new Uint8Array(e.memory.buffer)[initial+16]=108;frame=snapshotMemory(e.memory);
    const data=new Uint8Array(e.data_memory_1.buffer);let remaining=value,offset=1;
    do{const byte=Number(remaining&127n);remaining>>=7n;data[offset++]=byte|(remaining?128:0);}while(remaining);
    for(let i=1;i<=3;i++)images[i]=snapshotMemory(e[`data_memory_${i}`]);
    assert.equal(runtime.pendingPrints,0);fs.writeSync(1,bytes);
});
initial=runtime.instance.exports.test_stack_top_0.value;
let error;try{runtime.run();}catch(failure){error=failure;}
if(!(error instanceof GooseFailure)){if(error)throw error;assert.fail('LEB corrupted count guard did not fail');}
assert(error.message.includes('out of memory growing data storage'),error.message);
const e=runtime.instance.exports;assert.equal(seen,1);assert.equal(runtime.pendingPrints,0);
assert.equal(e.test_stack_top_0.value,initial,'LEB failed activation frame differs');
assert.equal(e.test_stack_top_1.value,1411,'LEB failed source top differs');
for(let i=2;i<=3;i++)assert.equal(e[`test_stack_top_${i}`].value,1,'LEB failure allocated receiver');
assert(snapshotMemory(e.memory).equals(frame),'LEB failed memory 0 image differs');
for(let i=1;i<=3;i++)assert(snapshotMemory(e[`data_memory_${i}`]).equals(images[i]),'LEB failed data image differs');
