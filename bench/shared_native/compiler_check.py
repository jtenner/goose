#!/usr/bin/env python3
"""Sequential compiler-check experiment. Without --run, only print the plan."""
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

CASES = ('ordinary', 'calls', 'arrays', 'deferred')


def source_for(globals_count, functions_count, case='ordinary', stdlib=False, named_return=False):
    source = 'import std;\n' if stdlib else ''
    source += ''.join(f'let g{i}:i64={i};\n' for i in range(globals_count))
    if named_return or case == 'deferred':
        source += 'fn destination()->i64{0}\nfn unused_return(){return 7 from destination;}\n'
    if case == 'calls':
        source += 'fn compute<T>(v:T)->T{var x:T=v;x+=1;return x;}\n'
    if case == 'deferred':
        source += 'let FLAG=true;\n'
    for i in range(functions_count):
        value = f'g{i % globals_count}' if globals_count else str(i)
        body = f'var x:i64={value};x+=1;return x;'
        if case == 'calls':
            body = f'var x=compute({value});x+=compute(1);return x;'
        elif case == 'arrays':
            body = f'let a:i64[2]=[{value},{i}];return a[0]+a[1];'
        elif case == 'deferred':
            body = f'let r=&FLAG;var x:i64={value};x+=1;const if true{{return 7 from destination;}}'
        source += f'fn check_fn_{i}()' + ('' if case == 'deferred' else '->i64') + '{' + body + '}\n'
    return source + 'fn main(){}\n'


def identity(path):
    path = path.resolve()
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                version=subprocess.check_output([path, 'version'], text=True).strip())


def aggregate(data):
    seconds = [x['seconds'] for x in data]
    center = statistics.median(seconds)
    return dict(median_seconds=center, seconds_mad=statistics.median(abs(x-center) for x in seconds),
                seconds_min=min(seconds), seconds_max=max(seconds),
                median_peak_rss_kib=statistics.median(x['process_peak_rss_kib'] for x in data), samples=data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--extended', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--globals', dest='globals_count', type=int, default=500)
    parser.add_argument('--functions', type=int, default=1000)
    parser.add_argument('--sizes', nargs='+', type=int, help='function counts, instead of --functions')
    parser.add_argument('--case', choices=CASES, action='append')
    parser.add_argument('--stdlib', action='store_true', help='include import std in every generated source')
    parser.add_argument('--named-return', action='store_true', help='include an unrelated named-return helper')
    parser.add_argument('--source', type=Path, action='append', help='measure existing sources instead of generated cases')
    parser.add_argument('--samples', type=int, default=7)
    parser.add_argument('--warmups', type=int, default=2)
    ns = parser.parse_args()
    sizes = ns.sizes or [ns.functions]
    if ns.globals_count < 0 or min(sizes) < 0 or ns.samples < 1 or ns.warmups < 0:
        parser.error('counts must be nonnegative; samples must be positive')
    if ns.run and not (ns.output and ns.baseline and ns.extended):
        parser.error('--run requires --baseline, --extended and --output')
    sources = [(dict(case=case, globals=ns.globals_count, unused_functions=size,
                     stdlib=ns.stdlib, named_return=ns.named_return),
                source_for(ns.globals_count, size, case, ns.stdlib, ns.named_return), None)
               for case in (ns.case or ['ordinary']) for size in sizes]
    if ns.source:
        sources = [(dict(source=str(path.resolve())), path.read_text(), path.resolve()) for path in ns.source]
    report = dict(platform=platform.platform(), affinity=sorted(os.sched_getaffinity(0)),
                  samples=ns.samples, warmups=ns.warmups, run_requires_explicit_flag=True,
                  measure='process wall seconds for check; no C generation',
                  sources=[dict(**meta, source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                                source_bytes=len(source.encode())) for meta, source, _ in sources], results=[])
    # A plan needs no compiler and launches no process. Fingerprint binaries only
    # inside the explicitly coordinated measurement phase.
    if not ns.run:
        print(json.dumps(report, indent=2))
        return
    if not Path('/usr/bin/time').exists():
        parser.error('GNU /usr/bin/time is required for RSS')
    report.update(baseline=identity(ns.baseline), extended=identity(ns.extended))
    with tempfile.TemporaryDirectory(prefix='goose-compiler-measure-') as directory:
        root = Path(directory)
        for source_index, (_, source, original_path) in enumerate(sources):
            input_file = original_path or root / 'ordinary.goose'
            if not original_path:
                input_file.write_text(source)
            for level in ('-O0', '-O2'):
                values = dict(baseline=[], extended=[])
                for index in range(ns.warmups + ns.samples):
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
                        if index >= ns.warmups:
                            values[name].append(dict(seconds=elapsed, process_peak_rss_kib=int(rss.read_text())))
                for name, data in values.items():
                    report['results'].append(dict(implementation=name, goose_optimization=level,
                                                  source_index=source_index, **aggregate(data)))
            assert hashlib.sha256(input_file.read_bytes()).hexdigest() == report['sources'][source_index]['source_sha256']
    assert identity(ns.baseline) == report['baseline']
    assert identity(ns.extended) == report['extended']
    ns.output.write_text(json.dumps(report, indent=2) + '\n')
    print(str(ns.output))


if __name__ == '__main__':
    main()
