// Observe snapshot owners while the guest is still active, before run's
// terminal cleanup could hide a missed release on a nonlocal exit.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { instantiate as production } from '../scripts/run_wasm.mjs';
const [modulePath, mode = ''] = process.argv.slice(2);
let instantiate = production;
if (mode) {
    let source = fs.readFileSync(new URL('../scripts/run_wasm.mjs', import.meta.url), 'utf8');
    if (mode === 'missing-drop') {
        assert(source.includes('if (!snapshots?.delete(snapshot))'));
        source = source.replace('if (!snapshots?.delete(snapshot))', 'if (!snapshots?.has(snapshot))');
    } else if (mode === 'alias-snapshot') {
        assert(source.includes('const value = Buffer.from(readMemory(identity, offset, length));'));
        source = source.replace('const value = Buffer.from(readMemory(identity, offset, length));',
                                'const value = readMemory(identity, offset, length);');
    } else throw new Error('unknown byte-snapshot control');
    const control = path.resolve(modulePath + '.' + mode + '.mjs');
    fs.writeFileSync(control, source);
    instantiate = (await import(pathToFileURL(control))).instantiate;
}
let runtime;
const output = [];
runtime = instantiate(fs.readFileSync(modulePath), bytes => {
    assert.equal(runtime.pendingPrints, 0, 'unfinished print line at completion');
    const line = bytes.toString('utf8');
    if (line === 'nested\n') assert.equal(runtime.pendingSnapshots, 1, 'outer byte snapshot owner missing');
    else assert.equal(runtime.pendingSnapshots, 0, 'unreleased byte snapshot at owner completion');
    if (line.startsWith('capture='))
        assert.equal(line, 'capture=abc|0|Xbc\n', 'byte argument was not captured before later effects');
    output.push(bytes);
});
runtime.run();
process.stdout.write(Buffer.concat(output));
