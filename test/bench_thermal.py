#!/usr/bin/env python3
"""Thermal tests use scripted sensors/virtual waits, never host temperature."""
import pathlib
import subprocess
import tempfile
import sys
import os
import json

root = pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='goose-thermal-test-') as tmp:
    folder = pathlib.Path(tmp)
    driver = folder / 'driver'
    subprocess.run(['c++', '-std=c++20', '-O2', str(root / 'test/bench_thermal.cpp'), str(root / 'src/bench_report.cpp'), '-o', str(driver)], check=True)
    child = folder / 'child'
    child.write_text('''#!/usr/bin/env python3
import os, pathlib, signal, socket, sys, time
s = socket.socket(fileno=int(sys.argv[2]))
s.sendall(b'READY\\n')
n = 0
while True:
    c = s.recv(1)
    if c != b'C': break
    n += 1
    start = time.monotonic_ns()
    failure = os.environ.get('THERMAL_FAILURE')
    if failure:
        folder = pathlib.Path(os.environ['THERMAL_ARTIFACTS'])
        # Wait for an in-call sensor read before the requested failure.
        while len((folder / 'temperature.log').read_text().splitlines()) < 3:
            time.sleep(.001)
        if failure == 'crash': os._exit(7)
        if failure == 'protocol':
            s.sendall(b'invalid timed result\\n')
        if failure == 'interrupt': os.kill(os.getppid(), signal.SIGINT)
        if failure == 'sensor': (folder / 'temp1_input').unlink()
        while True: time.sleep(.001)
    marker = os.environ.get('THERMAL_MARKER')
    if marker:
        while not os.path.exists(marker): time.sleep(.001)
    end = time.monotonic_ns() + 100
    value = n if os.environ.get('THERMAL_MISMATCH') else 1
    s.sendall(f'{start} {end} 1 4096 i64:{value};\\n'.encode())
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
        ('mismatch', 1, 1, 'checksum disagreement'),
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
    for failure, code, error in [('crash', 1, 'child_exit'), ('timeout', 1, 'timeout'),
                                 ('interrupt', 130, 'interrupted'), ('protocol', 1, 'protocol'),
                                 ('sensor', 1, 'sensor')]:
        artifacts = folder / ('failure-' + failure)
        artifacts.mkdir()
        env = dict(os.environ, THERMAL_FAILURE=failure, THERMAL_ARTIFACTS=str(artifacts))
        result = subprocess.run([str(driver), str(child), str(artifacts), 'failure-' + failure],
                                capture_output=True, text=True, env=env, timeout=10)
        assert result.returncode == code, (failure, result.stdout, result.stderr)
        report = json.loads((artifacts / 'report.json').read_text())
        row = report['results'][0]
        attempt, = row['attempts']
        assert attempt['status'] == ('interrupted' if code == 130 else 'failed')
        assert attempt['error']['code'] == error, (failure, attempt)
        assert attempt['elapsed_ns'] is None and attempt['seconds'] is None and attempt['checksum'] is None
        trace = [line.split('\t') for line in (artifacts / 'temperature.log').read_text().splitlines()]
        expected = [{'sensor_id': path, 'time_ns': ns, 'c': float(c)} for ns, path, c in trace[1:]]
        assert len(expected) >= 2 and attempt['temperature_reads'] == expected, (failure, attempt, trace)
        assert attempt['temperature_before_c'] == attempt['temperature_max_observed_c'] == row['temperature_max_observed_c'] == 60
        assert attempt['temperature_after_c'] is None and attempt['temperature_max_poll_gap_ms'] > 0
    print('benchmark thermal: 11 scripted scenarios, 5 failure-evidence scenarios, and monitor checks passed')
