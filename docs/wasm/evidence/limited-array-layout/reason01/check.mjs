import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate, GooseFailure } from '/home/dev/Projects/goose-wasm-backend/scripts/run_wasm.mjs';
const rt = instantiate(fs.readFileSync(process.argv[2]), bytes => fs.writeSync(1, bytes));
assert.throws(() => rt.run(), error => error instanceof GooseFailure && /^goose runtime error: array capacity exceeded(?: at |$)/.test(error.message), 'capacity conversion must report array capacity exceeded');
