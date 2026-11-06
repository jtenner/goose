#!/usr/bin/env node
// Initial Goose Wasm host ABI. Each invocation owns one isolated instance.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export class GooseFailure extends Error {}
export class GooseExit extends Error {
    constructor(code) { super(`exit(${code})`); this.code = code; }
}

// Native Goose spells shortest round-trip digits using its own decimal-point
// and exponent thresholds. f32 digits must round back to the original f32.
export function formatFloat(value, width) {
    if (Number.isNaN(value)) return 'nan';
    if (!Number.isFinite(value)) return value < 0 ? '-inf' : 'inf';
    const negative = value < 0 || Object.is(value, -0);
    const sign = negative ? '-' : '';
    const magnitude = Math.abs(value);
    if (!magnitude) return sign + '0.0';
    let decimal = magnitude.toString();
    if (width === 32) {
        for (let n = 1; n <= 9; n++) {
            const candidate = magnitude.toPrecision(n);
            if (Math.fround(Number(candidate)) === magnitude) { decimal = candidate; break; }
        }
    }
    const [mantissa, exponent = '0'] = decimal.split('e');
    let k = (mantissa.includes('.') ? mantissa.indexOf('.') : mantissa.length) + Number(exponent);
    let digits = mantissa.replace('.', '');
    while (digits[0] === '0') { digits = digits.slice(1); k--; }
    digits = digits.replace(/0+$/, '');
    const x = k - 1;
    if (x < -4 || x >= Math.max(digits.length, 15)) {
        const fraction = digits.length > 1 ? '.' + digits.slice(1) : '';
        return sign + digits[0] + fraction + 'e' + (x < 0 ? '-' : '+') + String(Math.abs(x)).padStart(2, '0');
    }
    if (x < 0) return sign + '0.' + '0'.repeat(-x - 1) + digits;
    if (digits.length <= k) return sign + digits.padEnd(k, '0') + '.0';
    return sign + digits.slice(0, k) + '.' + digits.slice(k);
}

export function instantiate(bytes, write = b => fs.writeSync(1, b)) {
    const pending = new Map();
    let serial = 0;
    let instance;
    let started = false;
    const pieces = token => {
        const value = pending.get(token);
        if (!value) throw new GooseFailure('invalid print token');
        return value;
    };
    const read = (offset, length) => {
        // Wasm passes i32 values signed. Treat address bits as memory32 offsets.
        offset >>>= 0; length >>>= 0;
        const buffer = instance.exports.memory.buffer;
        if (offset > buffer.byteLength || length > buffer.byteLength - offset)
            throw new GooseFailure('host byte range is outside Memory 0');
        return Buffer.from(buffer, offset, length);
    };
    const imports = { goose: {
        print_begin_v1() {
            // A token denotes a pending line, not a guest pointer. Nested prints
            // get independent buffers; only completed lines reach the sink.
            if (serial === 0x7fffffff) throw new GooseFailure('print token limit exceeded');
            const token = ++serial;
            pending.set(token, []);
            return token;
        },
        print_int_v1(token, value, unsigned) {
            pieces(token).push(Buffer.from((unsigned ? BigInt.asUintN(64, value) : value).toString()));
        },
        print_float_v1(token, value, width) { pieces(token).push(Buffer.from(formatFloat(value, width))); },
        print_bool_v1(token, value) { pieces(token).push(Buffer.from(value ? 'true' : 'false')); },
        print_bytes_v1(token, offset, length) { pieces(token).push(Buffer.from(read(offset, length))); },
        print_end_v1(token) {
            const line = pieces(token);
            pending.delete(token);
            line.push(Buffer.from('\n'));
            write(Buffer.concat(line));
        },
        fail_v1(code, offset, length, line) {
            const messages = { 1: 'assert failed', 2: 'division by zero',
                3: 'integer division overflow', 4: 'null reference', 5: 'out of memory growing frame storage' };
            const source = read(offset, length).toString('utf8');
            throw new GooseFailure(`goose runtime error: ${messages[code] ?? 'unknown failure'}${source ? ` at ${source}:${line}` : ''}`);
        },
        exit_v1(code) { throw new GooseExit(code); },
        fmod_v1(a, b) { return a % b; },
        float_to_int_v1(value) {
            if (!Number.isFinite(value)) return 0n;
            return BigInt.asIntN(64, BigInt(Math.trunc(value)));
        },
    } };
    instance = new WebAssembly.Instance(new WebAssembly.Module(bytes), imports);
    return {
        instance,
        get pendingPrints() { return pending.size; },
        run() {
            if (started) throw new GooseFailure('a Goose instance can be started only once; reentry is not supported');
            started = true;
            try { instance.exports._start(); }
            finally { pending.clear(); }
        },
    };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
    if (process.argv.length !== 3) {
        console.error('usage: node scripts/run_wasm.mjs program.wasm');
        process.exitCode = 2;
    } else {
        try { instantiate(fs.readFileSync(process.argv[2])).run(); }
        catch (e) {
            if (e instanceof GooseExit) process.exitCode = e.code & 255;
            else { console.error(e.message); process.exitCode = 1; }
        }
    }
}
