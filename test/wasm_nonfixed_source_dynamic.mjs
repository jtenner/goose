import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
let runtime, initial, frame, images, visits=0;
const labels=['before','after','between','before','after','done'];
runtime=instantiate(fs.readFileSync(process.argv[2]),bytes=>{
    const label=Buffer.from(bytes).toString('utf8').trim(),e=runtime.instance.exports;
    assert.equal(label,labels[visits]);
    assert.equal(e.test_stack_top_0.value,initial,'nonfixed dynamic frame top differs');
    assert.equal(e.test_stack_top_1.value,49,'nonfixed dynamic source top differs');
    if(visits===0){
        for(const memory of [e.data_memory_1,e.data_memory_2,e.data_memory_3])
            if(memory.buffer.byteLength===0)memory.grow(1);
        new Uint8Array(e.memory.buffer)[initial+16]=108;frame=snapshotMemory(e.memory);
        const sv=new Uint8Array(e.data_memory_1.buffer);sv.fill(199,33,49);sv.fill(212,49);
        images=[e.data_memory_1,e.data_memory_2,e.data_memory_3].map(memory=>snapshotMemory(memory));
        assert.equal(images[0].readUInt32LE(1),5);assert.equal(images[0].readUInt32LE(5),3);
        for(const [i,n] of [7n,-8n,900n].entries())assert.equal(images[0].readBigInt64LE(9+i*8),n);
    }
    if(label==='before'){
        const target=visits===0?2:3,memory=e[`data_memory_${target}`];
        if(visits===3){
            assert.equal(e.test_stack_top_2.value,6,'nonfixed dynamic caller top differs');
            images[1].writeUInt32LE(1,1);images[1][5]=91;
            assert.deepEqual(snapshotMemory(e.data_memory_2).subarray(0,6),images[1].subarray(0,6),'nonfixed dynamic caller image differs');
            new Uint8Array(e.data_memory_2.buffer).fill(212,6);images[1]=snapshotMemory(e.data_memory_2);
        }
        assert.equal(e[`test_stack_top_${target}`].value,1,'nonfixed dynamic allocated before checkpoint');
        const tv=new Uint8Array(memory.buffer);tv.fill(165,1);tv[27]=108;
        images[target-1]=snapshotMemory(memory);images[target-1].writeUInt16LE(3,1);
        images[0].copy(images[target-1],3,9,33);
    }else{
        if(label==='after'){
            const target=visits===1?2:3;
            assert.equal(e[`test_stack_top_${target}`].value,27,'nonfixed dynamic receiver top differs');
        }else if(label==='between'){
            assert.equal(e.test_stack_top_2.value,1,'nonfixed dynamic completed receiver top differs');
            assert.equal(e.test_stack_top_3.value,1,'nonfixed dynamic unused stack top differs');
        }else{
            assert.equal(e.test_stack_top_2.value,6,'nonfixed dynamic caller top differs');
            assert.equal(e.test_stack_top_3.value,1,'nonfixed dynamic completed receiver top differs');
        }
        assert.deepEqual(snapshotMemory(e.memory),frame,'nonfixed dynamic memory 0 image differs');
        for(let i=0;i<3;i++)assert.deepEqual(snapshotMemory(e[`data_memory_${i+1}`]),images[i],
            i===0?'nonfixed dynamic source image differs':'nonfixed dynamic receiver image differs');
    }
    assert.equal(runtime.pendingPrints,0);visits++;fs.writeSync(1,bytes);
});
initial=runtime.instance.exports.test_stack_top_0.value;runCompleted(runtime);assert.equal(visits,6);
const e=runtime.instance.exports;assert.equal(e.test_stack_top_0.value,initial);
for(let i=1;i<=3;i++)assert.equal(e[`test_stack_top_${i}`].value,1,'nonfixed dynamic final owner top differs');
assert.deepEqual(snapshotMemory(e.memory),frame);
for(let i=0;i<3;i++)assert.deepEqual(snapshotMemory(e[`data_memory_${i+1}`]),images[i]);
if(process.argv[3])fs.writeFileSync(process.argv[3],JSON.stringify({initial}));
