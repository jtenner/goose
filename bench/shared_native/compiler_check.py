#!/usr/bin/env python3
"""One-at-a-time before/after compiler check experiment; explicit --run only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import tempfile
import time


def identity(path):
    path = path.resolve()
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                version=subprocess.check_output([path, 'version'], text=True).strip())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--extended', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--run', action='store_true')
    ns = parser.parse_args()
    globals_count, functions_count, samples, warmups = 500, 1000, 7, 2
    report = dict(platform=platform.platform(), affinity=sorted(os.sched_getaffinity(0)),
                  globals=globals_count, unused_functions=functions_count,
                  samples=samples, warmups=warmups, measure='process wall seconds for check; no C generation',
                  baseline=identity(ns.baseline), extended=identity(ns.extended), results=[])
    report['source_generator'] = ('let g{i}:i64={i}; for i in range(500), then '
                                  'fn check_fn_{i}()->i64{var x:i64=g{i%500};x+=1;return x;} for i in range(1000), '
                                  'then fn main(){}; each declaration on its own line')
    source = ''.join(f'let g{i}:i64={i};\n' for i in range(globals_count))
    source += ''.join(f'fn check_fn_{i}()->i64{{var x:i64=g{i%globals_count};x+=1;return x;}}\n'
                      for i in range(functions_count))
    source += 'fn main(){}\n'
    report['source_sha256'] = hashlib.sha256(source.encode()).hexdigest()
    if not ns.run:
        print(json.dumps(report, indent=2))
        return
    if not ns.output:
        parser.error('--run requires --output')
    if not Path('/usr/bin/time').exists():
        parser.error('GNU /usr/bin/time is required for RSS')
    with tempfile.TemporaryDirectory(prefix='goose-compiler-measure-') as directory:
        root = Path(directory)
        input_file = root / 'ordinary.goose'
        input_file.write_text(source)
        for level in ('-O0', '-O2'):
            values = dict(baseline=[], extended=[])
            for index in range(warmups + samples):
                order = ['baseline', 'extended'] if index % 2 == 0 else ['extended', 'baseline']
                for name in order:
                    rss = root / 'rss'
                    argv = ['/usr/bin/time', '-f', '%M', '-o', str(rss), report[name]['path'],
                            'check', level, str(input_file)]
                    start = time.perf_counter()
                    result = subprocess.run(argv, capture_output=True, text=True, timeout=180)
                    elapsed = time.perf_counter() - start
                    assert result.returncode == 0 and 'typechecked ok' in result.stdout + result.stderr, (
                        name, result.returncode, result.stdout, result.stderr)
                    if index >= warmups:
                        values[name].append(dict(seconds=elapsed, process_peak_rss_kib=int(rss.read_text())))
            for name, data in values.items():
                seconds = [x['seconds'] for x in data]
                center = statistics.median(seconds)
                report['results'].append(dict(implementation=name, goose_optimization=level,
                    median_seconds=center, seconds_mad=statistics.median(abs(x-center) for x in seconds),
                    seconds_min=min(seconds), seconds_max=max(seconds),
                    median_peak_rss_kib=statistics.median(x['process_peak_rss_kib'] for x in data),
                    samples=data))
    assert identity(ns.baseline) == report['baseline']
    assert identity(ns.extended) == report['extended']
    ns.output.write_text(json.dumps(report, indent=2) + '\n')
    print(str(ns.output))


if __name__ == '__main__':
    main()
