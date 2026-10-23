#!/usr/bin/env python3
"""Phase9 acceptance: real Wasm fixtures, independent x86 bytes, failure stress.
Run: python3 test/parallel_wasm.py /absolute/path/to/goose
"""
import argparse
from pathlib import Path
import random
import re
import shutil
import struct
import tempfile
from native_examples_support import ROOT, build, run


def uleb(n):
    out = bytearray()
    while True:
        b = n & 127
        n >>= 7
        out.append(b | (128 if n else 0))
        if not n:
            return bytes(out)


def sleb(n):
    out = bytearray()
    while True:
        b = n & 127
        n >>= 7
        done = (n == 0 and b < 64) or (n == -1 and b >= 64)
        out.append(b | (0 if done else 128))
        if done:
            return bytes(out)


def section(kind, data):
    return bytes([kind]) + uleb(len(data)) + data


def module(bodies):
    # All functions have the actual Wasm type () -> i32. No imports or exports.
    return (b"\0asm\1\0\0\0" + section(1, b"\1\x60\0\1\x7f") +
            section(3, uleb(len(bodies)) + b"\0" * len(bodies)) +
            section(10, uleb(len(bodies)) + b"".join(uleb(len(b)) + b for b in bodies)))


def expression(constants, explicit_return=False):
    body = bytearray(b"\0")  # empty locals vector
    native = bytearray()
    for i, value in enumerate(constants):
        body += b"\x41" + sleb(value)
        native += b"\xb8" + struct.pack("<I", value & 0xffffffff) + b"\x50"
        if i:
            body += b"\x6a"
            native += b"\x59\x58\x01\xc8\x50"
    body += (b"\x0f" if explicit_return else b"") + b"\x0b"
    native += b"\x58\xc3"
    return bytes(body), native.hex()


def parse(output):
    jobs = []
    summary = None
    for line in output.splitlines():
        fields = line.split()
        if fields[0] == "job":
            jobs.append((int(fields[1]), int(fields[2]), int(fields[3]), fields[4] if len(fields) > 4 else ""))
        elif fields[0] == "summary":
            summary = tuple(map(int, fields[1:]))
        else:
            raise AssertionError(line)
    assert summary is not None, output
    return jobs, summary


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("goose", type=Path)
    ap.add_argument("--jobs", type=int, default=3000)
    ap.add_argument("--goose-opt", choices=("0", "2"), default="2")
    ns = ap.parse_args()
    if ns.jobs < 40:
        ap.error("--jobs must be at least 40 for abort/shutdown coverage")
    rng = random.Random(901)
    with tempfile.TemporaryDirectory(prefix="goose-wasm-") as directory:
        root = Path(directory)
        app = build(ns.goose.resolve(), ROOT / "samples/parallel_wasm/main.goose", root / "wasm", "-O" + ns.goose_opt)
        generated = root / "wasm.c"
        run([ns.goose.resolve(), "--standalone", "-O0", ROOT / "samples/parallel_wasm/main.goose", "-o", generated])
        c = generated.read_text()
        claim_body = re.search(r"static(?: GS_INLINE)? void compile_jobs_g[^;]*?\{(.*?)^\}", c, re.S | re.M)
        assert claim_body, "expected non-inlined job loop for codegen inspection"
        assert re.search(r"__atomic_fetch_add\([^;]*__ATOMIC_RELAXED", claim_body[1])
        assert "gs_mutex_lock" not in claim_body[1]
        fixture = root / "module.wasm"
        def execute(data, workers, mode="normal", ok=True):
            fixture.write_bytes(data)
            return run([app, fixture, len(data), workers, mode], ok=ok)
        valid = [expression([rng.randint(-2147483648, 2147483647) for _ in range(rng.randint(1, 24))], i % 2 == 0)
                 for i in range(ns.jobs)]
        valid[:6] = [expression(x) for x in ([0], [-1], [2147483647], [-2147483648], [64, -65], [-1, 1])]
        for count in (0, 1, 3, ns.jobs):
            cases = valid[:count]
            data = module([x[0] for x in cases])
            expected = [(i, 2, 1, native) for i, (_, native) in enumerate(cases)]
            for workers in (0, 1, 2, 4, 8):
                jobs, summary = parse(execute(data, workers).stdout)
                assert jobs == expected, (count, workers, jobs[:3])
                assert summary == (count, count, 0), summary
        if shutil.which("node"):
            fixture.write_bytes(module([b for b, _ in valid]))
            run(["node", "-e", "new WebAssembly.Module(require('fs').readFileSync(process.argv[1]))", fixture])
        padded_zero = b"\x80\0\x41\x80\x80\x80\x80\0\x0b"
        for workers in (0, 8):
            jobs, _ = parse(execute(module([padded_zero]), workers).stdout)
            assert jobs == [(0, 2, 1, expression([0])[1])]
        # Legal depth boundary and unsupported valid local declarations.
        deep = b"\0" + b"\x41\1" * 128 + b"\x6a" * 127 + b"\x0b"
        deep_native = (b"\xb8\1\0\0\0\x50" * 128 + b"\x59\x58\1\xc8\x50" * 127 + b"\x58\xc3").hex()
        too_deep = b"\0" + b"\x41\1" * 129 + b"\x6a" * 128 + b"\x0b"
        for workers in (0, 8):
            jobs, _ = parse(execute(module([deep, too_deep]), workers).stdout)
            assert jobs == [(0, 2, 1, deep_native), (1, 3, 1, "")]
        # Reuse a parent process/module across 12 pool lifecycles; extra workers.
        repeated = execute(module([valid[0][0]]), 8, "repeat").stdout
        block, rounds = [], 0
        for line in repeated.splitlines():
            block.append(line)
            if line.startswith("summary "):
                jobs, summary = parse("\n".join(block))
                assert jobs == [(0, 2, 1, valid[0][1])] and summary == (1, 1, 0)
                block = []
                rounds += 1
        assert rounds == 12 and not block
        for data in (b"\0asm\1\0\0\0", module([])):
            jobs, summary = parse(execute(data, 8).stdout)
            assert jobs == [] and summary == (0, 0, 0)
        # Random malformed/unsupported bodies are framed in real Wasm sections.
        bad = [b"\0\x6a\x0b", b"\0\x41\x80", b"\0\x42\0\x0b", b"\0\x0b",
               b"\0\x41\xff\xff\xff\xff\x0f\x0b", b"\0\x41\0\x0b\0",
               b"\1\1\x7f\x41\0\x0b", b"\0\x41\0\x41\0\x0b"]
        cases = [(b, "") for b in bad] + valid[:100]
        rng.shuffle(cases)
        expected = [(i, 2 if native else 3, 1, native) for i, (_, native) in enumerate(cases)]
        for workers in (0, 1, 2, 4, 8):
            jobs, summary = parse(execute(module([b for b, _ in cases]), workers).stdout)
            assert jobs == expected and summary == (len(cases), len(cases), 0)
        for _ in range(40):
            bodies = [bytes(rng.randrange(256) for _ in range(rng.randrange(1, 60))) for _ in range(9)]
            data = module(bodies)
            assert parse(execute(data, 0).stdout)[0] == parse(execute(data, 8).stdout)[0]
        # Malformed framing rejected before spawning a pool.
        good = module([valid[0][0]])
        invalid = [b"", good[:7], b"bad!" + good[4:], good[:4] + b"\2" + good[5:],
                   good[:-1], good + b"\x01\0", good + b"\x0a\1\0",
                   b"\0asm\1\0\0\0\x01\xff\xff\xff\xff\x7f",
                   b"\0asm\1\0\0\0" + section(3, b"\1\1"),
                   b"\0asm\1\0\0\0" + section(10, b"\1\xff\xff\xff\xff\x0f"),
                   b"\0asm\1\0\0\0" + section(0, b"\1\xff"), module([b"\0" * 4097])]
        for data in invalid:
            execute(data, 4, ok=False)
        fixture.write_bytes(good)
        run([app, fixture, len(good) + 1, 4, "normal"], ok=False)  # reject past EOF
        run([app, fixture, len(good), -1, "normal"], ok=False)
        run([app, fixture, len(good), 65, "normal"], ok=False)
        # Abort after claiming output, then cleanup abandoned borrows before close.
        jobs, summary = parse(execute(module([b for b, _ in valid[:40]]), 4, "abort").stdout)
        assert jobs[0][1:3] == (4, 1) and summary[2] == 1, (jobs[:1], summary)
        assert all(j[2] == 1 and j[1] in (2, 4) for j in jobs)
        jobs, summary = parse(execute(module([b for b, _ in valid[:40]]), 1, "abort").stdout)
        assert jobs[0][1:3] == (4, 1) and all(j[1:3] == (5, 0) for j in jobs[1:])
        assert summary == (40, 1, 1)
        # Shutdown is gated before claims, so zero published results is deterministic.
        for workers in (0, 1, 2, 4, 8):
            jobs, summary = parse(execute(module([valid[0][0]] * 40), workers, "cancel").stdout)
            assert all(j[1:3] == (5, 0) for j in jobs) and summary == (40, 0, 0)
        assert execute(module([]), 2, "faults").stdout.strip() == "faults ok"
    print("parallel Wasm acceptance passed")


if __name__ == "__main__":
    main()
