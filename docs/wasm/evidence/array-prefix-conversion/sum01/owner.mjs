import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '/home/dev/Projects/goose-wasm-backend/scripts/run_wasm.mjs';
import { runCompleted } from '/home/dev/Projects/goose-wasm-backend/test/wasm_reference_abi.mjs';
import { snapshotMemory } from '/home/dev/Projects/goose-wasm-backend/test/wasm_memory_snapshot.mjs';
const mode = process.argv[3];
const plans = { width:[1,2,3,8], leb_source:[2,2,128,1], leb_target:[2,2,128,1], empty:[1,2,0,1], overflow:[4,8,3,8] };
assert(mode in plans);
const [sourcePrefix,targetPrefix,count,stride] = plans[mode], payload=count*stride;
let runtime, initial, frame, source, target, visits=0;
runtime=instantiate(fs.readFileSync(process.argv[2]),bytes=>{
    const label=Buffer.from(bytes).toString('utf8').trim(),e=runtime.instance.exports;
    assert.equal(e.test_stack_top_0.value,initial,'prefix conversion live frame top differs');
    assert.equal(e.test_stack_top_1.value,1+sourcePrefix+payload,'prefix conversion source top differs');
    if(label==='before'){
        assert.equal(visits++,0);assert.equal(e.test_stack_top_2.value,1,'prefix conversion allocated before checkpoint');
        const sv=new Uint8Array(e.data_memory_1.buffer),tv=new Uint8Array(e.data_memory_2.buffer);
        sv.fill(0xd4,1+sourcePrefix+payload);tv.fill(0xa5,1);tv[1+targetPrefix+payload]=0x6c;
        new Uint8Array(e.memory.buffer)[initial+16]=0x6c;
        frame=snapshotMemory(e.memory);source=snapshotMemory(e.data_memory_1);target=snapshotMemory(e.data_memory_2);
        if(mode==='leb_source')assert.deepEqual([...source.subarray(1,3)],[128,1]);
        else if(mode==='empty')assert.equal(source[1],0);
        else if(sourcePrefix===1)assert.equal(source[1],count);
        else if(sourcePrefix===8)assert.equal(source.readBigUInt64LE(1),BigInt(count));
        else if(sourcePrefix===4)assert.equal(source.readUInt32LE(1),count);else assert.equal(source.readUInt16LE(1),count);
        if(mode==='leb_target'){target[1]=128;target[2]=1;}else if(targetPrefix===8)target.writeBigUInt64LE(BigInt(count),1);else if(targetPrefix===4)target.writeUInt32LE(count,1);else target.writeUInt16LE(count,1);
        source.copy(target,1+targetPrefix,1+sourcePrefix,1+sourcePrefix+payload);
    }else{
        assert.equal(label,'after');assert.equal(visits++,1);
        assert.equal(e.test_stack_top_2.value,1+targetPrefix+payload,'prefix conversion receiver top differs');
        assert.deepEqual(snapshotMemory(e.memory),frame,'prefix conversion memory 0 image differs');
        assert.deepEqual(snapshotMemory(e.data_memory_1),source,'prefix conversion source image differs');
        assert.deepEqual(snapshotMemory(e.data_memory_2),target,'prefix conversion receiver image differs');
    }
    assert.equal(runtime.pendingPrints,0);fs.writeSync(1,bytes);
});
initial=runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime);assert.equal(visits,2);
const e=runtime.instance.exports;
assert.equal(e.test_stack_top_0.value,initial,'prefix conversion completed frame top differs');
assert.equal(e.test_stack_top_1.value,1,'prefix conversion completed source top differs');
assert.equal(e.test_stack_top_2.value,1,'prefix conversion completed receiver top differs');
assert.deepEqual(snapshotMemory(e.memory),frame,'prefix conversion completed memory 0 image differs');
assert.deepEqual(snapshotMemory(e.data_memory_1),source,'prefix conversion completed source image differs');
assert.deepEqual(snapshotMemory(e.data_memory_2),target,'prefix conversion completed receiver image differs');

if(process.argv[4])fs.writeFileSync(process.argv[4],JSON.stringify({initial}));
