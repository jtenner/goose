import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const prefix=Number(process.argv[3]);assert([1,2,8].includes(prefix));
const payload=Buffer.from([1,11,0,22,0,2,33,0,44,0,0,0,2,3,55,0,66,0,0,0,0,0,0,0,0,4]);
const end=1+prefix+payload.length;
let runtime,initial,frame,data,visits=0;
runtime=instantiate(fs.readFileSync(process.argv[2]),bytes=>{
    const label=Buffer.from(bytes).toString('utf8').trim(),e=runtime.instance.exports;
    assert.equal(e.test_stack_top_0.value,initial,'aggregate prefix live frame top differs');
    if(label==='before'){
        assert.equal(visits++,0);assert.equal(e.test_stack_top_1.value,1,'aggregate prefix allocated before checkpoint');
        new Uint8Array(e.memory.buffer)[initial+16]=0x6c;
        const view=new Uint8Array(e.data_memory_1.buffer);view.fill(0xa5,1);view[end]=0xc5;
        frame=snapshotMemory(e.memory);data=snapshotMemory(e.data_memory_1);
        if(prefix===8)data.writeBigUInt64LE(2n,1);else if(prefix===2)data.writeUInt16LE(2,1);else data[1]=2;
        payload.copy(data,1+prefix);
    }else{
        assert.equal(label,'after');assert.equal(visits++,1);
        assert.equal(e.test_stack_top_1.value,end,'aggregate prefix live data top differs');
        assert.deepEqual(snapshotMemory(e.memory),frame,'aggregate prefix memory 0 image differs');
        assert.deepEqual(snapshotMemory(e.data_memory_1),data,'aggregate prefix data image differs');
    }
    assert.equal(runtime.pendingPrints,0);fs.writeSync(1,bytes);
});
initial=runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime);assert.equal(visits,2);
const e=runtime.instance.exports;
assert.equal(e.test_stack_top_0.value,initial,'aggregate prefix completed frame top differs');
assert.equal(e.test_stack_top_1.value,1,'aggregate prefix completed data top differs');
assert.deepEqual(snapshotMemory(e.memory),frame,'aggregate prefix completed memory 0 image differs');
assert.deepEqual(snapshotMemory(e.data_memory_1),data,'aggregate prefix completed data image differs');
if(process.argv[4])fs.writeFileSync(process.argv[4],JSON.stringify({initial,prefix,end}));
