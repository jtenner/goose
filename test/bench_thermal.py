#!/usr/bin/env python3
"""Thermal tests use scripted sensors/virtual waits, never host temperature."""
import pathlib
import subprocess
import tempfile
import sys
import os

root = pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='goose-thermal-test-') as tmp:
    folder = pathlib.Path(tmp)
    driver = folder / 'driver'
    subprocess.run(['c++', '-std=c++20', '-O2', str(root / 'test/bench_thermal.cpp'), '-o', str(driver)], check=True)
    child = folder / 'child'
    child.write_text('''#!/usr/bin/env python3
import os, socket, sys, time
s = socket.socket(fileno=int(sys.argv[2]))
s.sendall(b'READY\\n')
n = 0
while True:
    c = s.recv(1)
    if c != b'C': break
    n += 1
    start = time.monotonic_ns()
    marker = os.environ.get('THERMAL_MARKER')
    if marker:
        while not os.path.exists(marker): time.sleep(.001)
    end = time.monotonic_ns() + 100
    value = n if os.environ.get('THERMAL_MISMATCH') else 1
    s.sendall(f'{start} {end} 1 i64:{value};\\n'.encode())
''')
    child.chmod(0o755)
    for scenario, code, calls, marker in [
        ('adapter', 0, 0, 'scripted_cpu'),
        ('wait', 0, 6, 'gate_wait=2.000'),
        ('retry', 0, 7, 'thermal_rejected'),
        ('retry-process', 0, 7, 'thermal_rejected'),
        ('mid', 0, 7, 'maximum_observed_Tctl=70.000'),
        ('cancel', 130, 0, 'benchmark interrupted'),
        ('exhaust', 1, 1, 'thermal_retries exhausted'),
        ('absent', 2, 0, 'no readable Tctl'),
        ('off', 0, 6, 'UNGATED thermal_mode=disabled'),
        ('loss', 1, 0, 'temperature read failed'),
        ('mismatch', 1, 2, 'checksum disagreement'),
    ]:
        env = dict(os.environ)
        if scenario == 'mismatch': env['THERMAL_MISMATCH'] = '1'
        artifacts = folder / scenario
        artifacts.mkdir()
        if scenario == 'mid': env['THERMAL_MARKER'] = str(artifacts / 'crossed')
        result = subprocess.run([str(driver), str(child), str(artifacts), scenario], capture_output=True, text=True, env=env, timeout=10)
        assert result.returncode == code, (scenario, result.stdout, result.stderr)
        assert len(result.stdout.splitlines()) == calls, (scenario, result.stdout)
        assert marker in result.stderr, (scenario, result.stderr)
        if scenario in ('retry', 'retry-process', 'mid'):
            assert result.stderr.count('status=accepted') == 6
            assert result.stderr.count('warmup slot=1') == 2
            assert len(list(artifacts.glob('*.stdout'))) == (7 if scenario == 'retry-process' else 1)
        if scenario == 'absent': assert not list(artifacts.glob('*.stdout'))
    print('benchmark thermal: 11 scripted adapter/supervisor scenarios plus monitor, equality and timeout checks passed')
