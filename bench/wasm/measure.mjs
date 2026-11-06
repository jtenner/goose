// Initial scalar baseline. Called only by the coordinator's measurement script.
import fs from 'node:fs';
import { performance } from 'node:perf_hooks';
import { instantiate } from '../../scripts/run_wasm.mjs';
const bytes = fs.readFileSync(process.argv[2]);
const rows = [];
let answer;
for (let sample = -2; sample < 7; sample++) {
    const start = performance.now();
    const guest = instantiate(bytes, output => { answer = output.toString(); });
    const ready = performance.now();
    guest.run();
    const end = performance.now();
    rows.push({ sample, warmup: sample < 0, compile_and_init_ms: ready - start,
        run_ms: end - ready, memory0_bytes: guest.instance.exports.memory.buffer.byteLength });
}
console.log(JSON.stringify({ answer, node: process.version, v8: process.versions.v8,
    max_rss_kib: process.resourceUsage().maxRSS, rows }));
