import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate, GooseFailure } from '../scripts/run_wasm.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const overflow=process.argv[3]==='overflow',count=overflow?3:Number(process.argv[3]);assert(overflow||[256,65536].includes(count));
const width=overflow?8:count===256?2:4, payload=overflow?24:count;
let runtime,initial,frame,source,target,visits=0;
runtime=instantiate(fs.readFileSync(process.argv[2]),bytes=>{
    assert.equal(Buffer.from(bytes).toString('utf8'),'before\n','prefix conversion range executed after failure');
    assert.equal(visits++,0);
    const e=runtime.instance.exports;
    assert.equal(e.test_stack_top_0.value,initial,'prefix conversion range live frame differs');
    assert.equal(e.test_stack_top_1.value,1+width+payload,'prefix conversion range source top differs');
    assert.equal(e.test_stack_top_2.value,1,'prefix conversion range allocated receiver');
    const sv=new Uint8Array(e.data_memory_1.buffer),tv=new Uint8Array(e.data_memory_2.buffer);
    sv[1+width+payload]=0x6c;tv.fill(0xa5,1);
    frame=snapshotMemory(e.memory);source=snapshotMemory(e.data_memory_1);target=snapshotMemory(e.data_memory_2);
    assert.equal(width===8?Number(source.readBigUInt64LE(1)):width===2?source.readUInt16LE(1):source.readUInt32LE(1),count);
    if(overflow){source.writeBigUInt64LE(536870912n,1);new Uint8Array(e.data_memory_1.buffer).set(source);}
    else assert(source.subarray(1+width,1+width+payload).every(byte=>byte===73));
    assert.equal(runtime.pendingPrints,0);fs.writeSync(1,bytes);
});
initial=runtime.instance.exports.test_stack_top_0.value;
let failure;try{runtime.run();}catch(error){failure=error;}
if(!(failure instanceof GooseFailure)){if(failure)throw failure;assert.fail('prefix conversion range did not fail');}
assert.match(failure.message,overflow?/^goose runtime error: out of memory growing data storage(?: at |$)/:/^goose runtime error: array length exceeds stored prefix(?: at |$)/);
assert.equal(visits,1);
const e=runtime.instance.exports;
assert.equal(e.test_stack_top_0.value,initial,'prefix conversion range failed frame differs');
assert.equal(e.test_stack_top_1.value,1+width+payload,'prefix conversion range failed source differs');
assert.equal(e.test_stack_top_2.value,1,'prefix conversion range allocated receiver');
assert.deepEqual(snapshotMemory(e.memory),frame,'prefix conversion range memory 0 differs');
assert.deepEqual(snapshotMemory(e.data_memory_1),source,'prefix conversion range source image differs');
assert.deepEqual(snapshotMemory(e.data_memory_2),target,'prefix conversion range receiver image differs');
assert.equal(runtime.pendingPrints,0);assert.equal(runtime.pendingSnapshots,0);
assert.throws(()=>runtime.run(),error=>error instanceof GooseFailure&&/only once/.test(error.message));
