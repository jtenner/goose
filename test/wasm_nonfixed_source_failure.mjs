import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate, GooseFailure } from '../scripts/run_wasm.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const mode=process.argv[3];assert(['grow','runtime','product','sum'].includes(mode));
const width=mode==='grow'||mode==='runtime',grow=mode!=='runtime';
const count=width?256:3,prefix=grow?0:8,payload=width?256:24;
const sourceTop=1+prefix+payload,frameBytes=grow?16:0;
let runtime,initial,frame,source,target,visits=0;
runtime=instantiate(fs.readFileSync(process.argv[2]),bytes=>{
    const label=Buffer.from(bytes).toString('utf8').trim(),e=runtime.instance.exports;
    assert.equal(label,'before',width?'nonfixed range executed after failure':'nonfixed size guard executed after failure');
    assert.equal(visits++,0);assert.equal(e.test_stack_top_0.value,initial+frameBytes);
    assert.equal(e.test_stack_top_1.value,sourceTop);assert.equal(e.test_stack_top_2.value,1);
    for(const memory of [e.data_memory_1,e.data_memory_2])if(memory.buffer.byteLength===0)memory.grow(1);
    const mv=new Uint8Array(e.memory.buffer);mv[initial+frameBytes+16]=108;
    const before=snapshotMemory(e.memory);
    if(grow){assert.equal(before.readBigUInt64LE(initial),(1n<<32n)|1n);assert.equal(before.readBigUInt64LE(initial+8),BigInt(count));}
    if(!width)new DataView(e.memory.buffer).setBigUint64(initial+8,BigInt(mode==='product'?536870912:536870911),true);
    frame=snapshotMemory(e.memory);
    const sv=new Uint8Array(e.data_memory_1.buffer);sv.fill(212,sourceTop);source=snapshotMemory(e.data_memory_1);
    if(width){
        if(!grow){assert.equal(source.readUInt32LE(1),256);assert.equal(source.readUInt32LE(5),256);}
        assert.deepEqual(source.subarray(1+prefix,sourceTop),Buffer.alloc(256,73));
    }else for(const [i,n] of [7n,-8n,900n].entries())assert.equal(source.readBigInt64LE(1+i*8),n);
    const tv=new Uint8Array(e.data_memory_2.buffer);tv.fill(165,1);tv[33]=108;target=snapshotMemory(e.data_memory_2);
    assert.equal(runtime.pendingPrints,0);fs.writeSync(1,bytes);
});
initial=runtime.instance.exports.test_stack_top_0.value;
let failure;try{runtime.run();}catch(error){failure=error;}
if(!(failure instanceof GooseFailure)){if(failure)throw failure;assert.fail('nonfixed guard did not fail');}
assert(failure.message.includes(width?'array length exceeds stored prefix':'out of memory growing data storage'),failure.message);
const e=runtime.instance.exports;assert.equal(visits,1);assert.equal(runtime.pendingPrints,0);
assert.equal(e.test_stack_top_0.value,initial+frameBytes,'nonfixed failed activation frame changed');
assert.equal(e.test_stack_top_1.value,sourceTop,'nonfixed failed source top changed');
assert.equal(e.test_stack_top_2.value,1,'nonfixed failure allocated receiver');
assert.deepEqual(snapshotMemory(e.memory),frame,'nonfixed failure memory 0 image differs');
assert.deepEqual(snapshotMemory(e.data_memory_1),source,'nonfixed failure source image differs');
assert.deepEqual(snapshotMemory(e.data_memory_2),target,'nonfixed failure receiver image differs');
