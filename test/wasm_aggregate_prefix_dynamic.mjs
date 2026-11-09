import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const payload=Buffer.from([1,11,0,22,0,2,33,0,44,0,0,0,2,3,55,0,66,0,0,0,0,0,0,0,0,4]);
let runtime,initial,frame,one,two,visits=0;
runtime=instantiate(fs.readFileSync(process.argv[2]),bytes=>{
    const label=Buffer.from(bytes).toString('utf8').trim(),e=runtime.instance.exports;
    assert.equal(e.test_stack_top_0.value,initial,'aggregate dynamic frame top differs');
    if(label==='before'){
        assert(visits===0||visits===2);
        assert.equal(e.test_stack_top_1.value,visits===0?1:6,'aggregate dynamic caller top differs');
        assert.equal(e.test_stack_top_2.value,1,'aggregate dynamic future top differs');
        if(visits===0){new Uint8Array(e.memory.buffer)[initial+16]=0x6c;frame=snapshotMemory(e.memory);}
        else{
            assert.deepEqual(snapshotMemory(e.memory),frame,'aggregate dynamic memory 0 image differs');
            const old=snapshotMemory(e.data_memory_1);assert.equal(old.readUInt32LE(1),1);assert.equal(old[5],91);
            new Uint8Array(e.data_memory_1.buffer).fill(0xd4,6);
        }
        const memory=visits===0?e.data_memory_1:e.data_memory_2,view=new Uint8Array(memory.buffer);
        view.fill(0xa5,1);view[31]=0xc5;
        const expected=snapshotMemory(memory);expected.writeUInt32LE(2,1);payload.copy(expected,5);
        if(visits===0){one=expected;two=snapshotMemory(e.data_memory_2);}else{one=snapshotMemory(e.data_memory_1);two=expected;}
    }else{
        assert.equal(label,visits===4?'done':'after');
        assert.equal(e.test_stack_top_1.value,visits===1?31:6,'aggregate dynamic current top differs');
        assert.equal(e.test_stack_top_2.value,visits===3?31:1,'aggregate dynamic selected top differs');
        assert.deepEqual(snapshotMemory(e.memory),frame,'aggregate dynamic memory 0 image differs');
        assert.deepEqual(snapshotMemory(e.data_memory_1),one,'aggregate dynamic data image differs');
        assert.deepEqual(snapshotMemory(e.data_memory_2),two,'aggregate dynamic data image differs');
    }
    visits++;assert.equal(runtime.pendingPrints,0);fs.writeSync(1,bytes);
});
initial=runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime);assert.equal(visits,5);
const e=runtime.instance.exports;
for(let memory=0;memory<3;memory++)assert.equal(e[`test_stack_top_${memory}`].value,memory===0?initial:1,'aggregate dynamic completed top differs');
assert.deepEqual(snapshotMemory(e.memory),frame,'aggregate dynamic completed memory 0 image differs');
assert.deepEqual(snapshotMemory(e.data_memory_1),one,'aggregate dynamic completed caller image differs');
assert.deepEqual(snapshotMemory(e.data_memory_2),two,'aggregate dynamic completed callee image differs');
