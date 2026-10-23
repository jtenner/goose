#!/usr/bin/env python3
"""Execute the released measurement plans in order, retaining every artifact."""
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path('/home/dev/Projects/goose-const-if')
DEST = ROOT / 'bench/shared_native/results/deferred-state-2026-10-23'
PLAN = Path('/tmp/goose-perf-measure-plan-manifest.json')
EXPECTED = {
    '/home/dev/Projects/goose/build-pre-snapshot-fix/goose': 'c35d93ece5653cfd4d984295d91ac63db63c9b8873a3b6d10ea30503407ab327',
    str(ROOT / 'build-perf-release/goose'): '169c9d41d2506b1c4e302be64cba35941d473d441b5e7debfb4e8c3322ecbcf1',
    '/tmp/goose-upstream-baseline': 'f56ac3c31d3bbc1c200efc65d908063b9de9d4ae4127032c22f5432e9e8a5280',
}
SRC = '741cbecbd8b0f95e4ab9148161a5af870cb3ca12'
def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()
def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save():
    temp = DEST / 'commands.json.tmp'
    temp.write_text(json.dumps(manifest, indent=2) + '\n')
    temp.replace(DEST / 'commands.json')
def hash_artifacts():
    return {str(p.relative_to(DEST)): digest(p) for p in sorted(DEST.rglob('*'))
            if p.is_file() and p.name not in ('commands.json', 'commands.json.tmp', 'SHA256SUMS')}

assert git('rev-parse', 'HEAD:src') == SRC
assert not git('status', '--porcelain')
assert {path: digest(path) for path in EXPECTED} == EXPECTED
assert 0 in os.sched_getaffinity(0)
DEST.mkdir()
shutil.copyfile(__file__, DEST / 'collect.py')
shutil.copyfile(PLAN, DEST / 'released-plan-manifest.json')
plans = json.loads(PLAN.read_text())
env = dict(PATH='/home/dev/.local/share/mise/installs/clang/23.1.3/bin:/tmp/goose-return-alignment-toolchain:/home/dev/.local/bin:/usr/bin:/bin',
           HOME=os.environ['HOME'], LANG='C.UTF-8', LC_ALL='C.UTF-8', TMPDIR='/tmp',
           GOOSE_STDLIB=plans['GOOSE_STDLIB'])
manifest = dict(started_utc=now(), completed=False, execution_head=git('rev-parse', 'HEAD'),
                src_tree=SRC, effective_environment=env,
                environment_policy='Only these variables passed to each harness and its compiler children; all oracle/work/sanitizer variables absent.',
                cpu_model=next(line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')),
                requested_cpu=0, coordinator_affinity=sorted(os.sched_getaffinity(0)),
                binary_sha256_before={path: digest(path) for path in EXPECTED}, commands=[])
manifest['harness_sha256'] = digest(ROOT / 'bench/shared_native/compiler_check.py')
# Retain exact generated and actual input text in addition to hashes and generator.
spec = importlib.util.spec_from_file_location('compiler_check', ROOT / 'bench/shared_native/compiler_check.py')
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)
inputs = DEST / 'inputs'
inputs.mkdir()
for plan in plans['plans']:
    old_plan = json.loads(Path(plan['plan']).read_text())
    shutil.copyfile(plan['plan'], DEST / ('released-plan-' + plan['name'] + '.json'))
    for index, source in enumerate(old_plan['sources']):
        text = (Path(source['source']).read_text() if 'source' in source else
                harness.source_for(source['globals'], source['unused_functions'], source['case'], source['stdlib'], source['named_return']))
        path = inputs / f"{plan['name']}-{index:02}.goose"
        path.write_text(text)
        assert digest(path) == source['source_sha256']
# Hash shared standard library and actual sample dependencies. No compiler is run here.
dependencies = {}
for base in (Path(env['GOOSE_STDLIB']), Path('/home/dev/Projects/goose/samples/parallel_wasm')):
    for path in sorted(base.rglob('*')):
        if path.is_file():
            dependencies[str(path)] = digest(path)
(DEST / 'input-dependencies.json').write_text(json.dumps(dependencies, indent=2) + '\n')
save()
for plan in plans['plans']:
    output = DEST / (plan['name'] + '.json')
    argv = plan['argv'] + ['--run', '--output', str(output)]
    entry = dict(name=plan['name'], argv=argv, cwd=str(ROOT), started_utc=now(),
                 expected_check_processes=plan['compiler_check_processes'],
                 log=plan['name'] + '.log', status='running')
    manifest['commands'].append(entry)
    save()
    print(f"{now()} START {plan['name']} ({plan['compiler_check_processes']} check processes)", flush=True)
    with (DEST / entry['log']).open('w') as log:
        result = subprocess.run(argv, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
    entry.update(returncode=result.returncode, finished_utc=now())
    journal = output.with_suffix('.processes.jsonl')
    records = [json.loads(line) for line in journal.read_text().splitlines()] if journal.exists() else []
    entry['observed_check_processes'] = len(records)
    entry['status'] = 'passed' if result.returncode == 0 else 'FAILED'
    if result.returncode == 0:
        report = json.loads(output.read_text())
        assert report['completed'] and report['affinity'] == [0]
        assert len(records) == plan['compiler_check_processes']
        assert all(r['returncode'] == 0 for r in records)
        assert report['harness_sha256'] == manifest['harness_sha256']
        assert report['compiler_environment'] == dict(GOOSE_STDLIB=env['GOOSE_STDLIB'])
        assert not report['instrumentation_environment_removed']
    manifest['artifact_sha256'] = hash_artifacts()
    save()
    print(f"{now()} {entry['status']} {plan['name']} ({len(records)} check processes)", flush=True)
    if result.returncode:
        manifest['finished_utc'] = now()
        manifest['binary_sha256_after'] = {path: digest(path) for path in EXPECTED}
        save()
        sys.exit(result.returncode)
manifest['binary_sha256_after'] = {path: digest(path) for path in EXPECTED}
assert manifest['binary_sha256_after'] == manifest['binary_sha256_before'] == EXPECTED
assert git('rev-parse', 'HEAD:src') == SRC
assert sum(c['observed_check_processes'] for c in manifest['commands']) == 684
assert all(digest(path) == old for path, old in dependencies.items())
manifest.update(completed=True, finished_utc=now(), artifact_sha256=hash_artifacts())
save()
(DEST / 'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.relative_to(DEST)}\n' for p in sorted(DEST.rglob('*')) if p.is_file() and p.name != 'SHA256SUMS'))
print(f'{now()} COMPLETE 684/684 check processes; binary and input hashes unchanged', flush=True)
