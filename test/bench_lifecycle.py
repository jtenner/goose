#!/usr/bin/env python3
"""Supervisor lifecycle checks. No benchmark workload or timing runs."""
import fcntl
import json
import pathlib
import subprocess
import sys
import tempfile

root = pathlib.Path(__file__).resolve().parents[1]
exe = pathlib.Path(sys.argv[1]).resolve()
if sys.platform != 'linux':
    print('benchmark lifecycle: Linux only (skipped)')
    sys.exit(0)

with tempfile.TemporaryDirectory(prefix='goose-bench-lifecycle-') as name:
    folder = pathlib.Path(name)
    source = folder / 'entry.goose'
    source.write_text('bench "entry" fn entry() -> i64 { 1 }\n')
    marker = folder / 'compiler-started'
    compiler = folder / 'cc'
    compiler.write_text('#!/bin/sh\ntouch "' + str(marker) + '"\nexit 1\n')
    compiler.chmod(0o755)
    report = folder / 'report.json'
    # The command must reject contention before compiler discovery or builds.
    with open('/tmp/goose-shared-native-benchmark.lock', 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = subprocess.run([
            str(exe), 'bench', str(source), '--temperature', 'off',
            '--cc', str(compiler), '--json', str(report),
        ], capture_output=True, text=True, timeout=30)
        assert result.returncode == 2, (result.returncode, result.stdout, result.stderr)
        assert 'lock unavailable or occupied' in result.stderr, result.stderr
        assert not marker.exists(), 'occupied lock allowed compiler launch'
        assert json.loads(report.read_text())['error']['code'] == 'lock'
        listed = subprocess.run([str(exe), 'bench', str(source), '--list'],
                                capture_output=True, text=True, timeout=30)
        assert listed.returncode == 0, (listed.stdout, listed.stderr)
        assert not marker.exists()
    # Prove that the compiler probe detects a launch once the lock is free.
    result = subprocess.run([
        str(exe), 'bench', str(source), '--temperature', 'off', '--cc', str(compiler),
    ], capture_output=True, text=True, timeout=30)
    assert result.returncode == 2 and marker.exists(), (result.stdout, result.stderr)

print('benchmark lifecycle: occupied lock prevents compiler launch')
