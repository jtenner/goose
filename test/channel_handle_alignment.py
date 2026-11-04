#!/usr/bin/env python3
"""Alignment-one channel tokens in packed fields, arrays, returns and worker packets."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

SOURCE = r'''
struct Box { prefix: u8, handle: Channel<i64> }
fn pass(handle: Channel<i64>) -> Channel<i64> { handle }
fn choose(handles: Channel<i64>[2], i: i64) -> Channel<i64> { handles[i] }
thread_fn send(prefix: u8, handle: Channel<i64>) {
    assert(prefix == 3);
    assert(channel_send(handle, 41));
}
fn main() {
    let a = channel<i64>();
    let b = channel<i64>();
    let box = Box { 1, pass(a) };
    let handles = [box.handle, b];
    let id = thread_spawn(send, 3, choose(handles, 1));
    let value, ok = channel_receive(b);
    assert(ok && thread_wait(id));
    print(value);
}
'''

def check(exe=None):
    exe = exe or os.environ.get("GOOSE_TEST_EXE") or shutil.which("goose++")
    checks = 0
    with tempfile.TemporaryDirectory(prefix="channel-handle-alignment-") as td:
        root = Path(td)
        source = root / "handles.goose"
        source.write_text(SOURCE)
        for goose_level in (0, 2):
            cfile = root / f"handles-{goose_level}.c"
            result = subprocess.run([exe, f"-O{goose_level}", "--standalone", "-o", cfile, source],
                                    capture_output=True, text=True, timeout=120)
            assert result.returncode == 0, result.stdout + result.stderr
            for cc in (os.environ.get("CC", "gcc"), os.environ.get("CLANG", "clang")):
                binary = root / ("handles-" + Path(cc).name)
                result = subprocess.run([cc, f"-O{goose_level}", "-fsanitize=undefined",
                                         "-fno-sanitize-recover=all", cfile, "-lm", "-ldl",
                                         "-pthread", "-o", binary], capture_output=True,
                                        text=True, timeout=120)
                assert result.returncode == 0, result.stdout + result.stderr
                result = subprocess.run([binary], capture_output=True, text=True, timeout=30)
                assert result.returncode == 0, result.stdout + result.stderr
                assert result.stdout == "41\n", result.stdout
                checks += 1
    print(f"channel handle alignment: {checks} checks passed")

if __name__ == "__main__":
    check()
