import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const sameImage = (actual, expected, reason) => assert(actual.equals(expected), reason);
const [file,rawCount,record] = process.argv.slice(2), count=Number(rawCount);
assert(count===0||count===128);
const prefix=count?2:1, top=1+prefix+count*11, header=Buffer.from(count?[128,1]:[0]);
const cell=Buffer.alloc(11);cell[0]=34;cell.writeBigInt64LE(-8n,1);cell.writeUInt16LE(900,9);
let runtime,initial,frame,source,images=[],cycle=0,stage='before',visits=0;
function check(e){
    sameImage(snapshotMemory(e.memory),frame,'LEB copy memory 0 image differs');
    sameImage(snapshotMemory(e.data_memory_1),source,'LEB copy source image differs');
    for(let i=2;i<=3;i++)sameImage(snapshotMemory(e[`data_memory_${i}`]),images[i],'LEB copy receiver image differs');
}
runtime=instantiate(fs.readFileSync(file),bytes=>{
    const label=Buffer.from(bytes).toString('utf8').trim(),e=runtime.instance.exports;
    assert.equal(e.test_stack_top_0.value,initial,'LEB copy frame top differs');
    assert.equal(e.test_stack_top_1.value,top,'LEB copy live source top differs');
    if(label==='before'){
        assert.equal(stage,'before');
        assert.equal(e.test_stack_top_2.value,cycle?6:1,'LEB copy caller top differs');
        assert.equal(e.test_stack_top_3.value,1,'LEB copy future top differs');
        for(let i=2;i<=3;i++)if(!e[`data_memory_${i}`].buffer.byteLength)e[`data_memory_${i}`].grow(1);
        if(!cycle){
            const view=new Uint8Array(e.memory.buffer);view.fill(212,initial,initial+32);view[initial+16]=108;frame=snapshotMemory(e.memory);
            new Uint8Array(e.data_memory_1.buffer).fill(212,top);
            source=Buffer.alloc(e.data_memory_1.buffer.byteLength);header.copy(source,1);
            for(let i=0;i<count;i++)cell.copy(source,1+prefix+i*11);source.fill(212,top);
            sameImage(snapshotMemory(e.data_memory_1),source,'LEB independent source image differs');
        }else{
            const actual=snapshotMemory(e.data_memory_2);assert.equal(actual.readUInt32LE(1),1);assert.equal(actual[5],91);
            new Uint8Array(e.data_memory_2.buffer).fill(212,6);
        }
        const selected=cycle+2,target=new Uint8Array(e[`data_memory_${selected}`].buffer);target.fill(165,1);target[top]=197;
        for(let i=2;i<=3;i++)images[i]=snapshotMemory(e[`data_memory_${i}`]);
        source.copy(images[selected],1,1,top);stage='after';
    }else if(label==='after'){
        assert.equal(stage,'after');
        assert.equal(e.test_stack_top_2.value,cycle?6:top,'LEB copy first receiver top differs');
        assert.equal(e.test_stack_top_3.value,cycle?top:1,'LEB copy selected receiver top differs');
        check(e);stage=cycle?'done':'between';
    }else{
        assert.equal(label,stage);
        assert.equal(e.test_stack_top_2.value,cycle?6:1,'LEB completed receiver top differs');
        assert.equal(e.test_stack_top_3.value,1,'LEB completed receiver top differs');
        check(e);if(label==='between'){cycle++;stage='before';}else stage='complete';
    }
    visits++;assert.equal(runtime.pendingPrints,0);fs.writeSync(1,bytes);
});
initial=runtime.instance.exports.test_stack_top_0.value;runCompleted(runtime);assert.equal(visits,6);assert.equal(stage,'complete');
const e=runtime.instance.exports;
assert.equal(e.test_stack_top_0.value,initial,'LEB final frame top differs');
for(let i=1;i<=3;i++)assert.equal(e[`test_stack_top_${i}`].value,1,'LEB final data top differs');
check(e);if(record)fs.writeFileSync(record,JSON.stringify({initial,count,prefix,top,bytes:top-1}));
