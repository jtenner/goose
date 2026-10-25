"""Read native Goose JSON v1 results without running or timing a workload.

The caller owns work units, cross-language checks, and experiment ordering.
Only complete rows with valid counts and policy can enter a comparison.
"""
import hashlib
import json
import math
import re
import struct
import subprocess
from pathlib import Path
from fractions import Fraction
from statistics import median


class InvalidResult(ValueError):
    pass


def decoded_checksum(checksum):
    """Decode ordered scalars. Do not merge components or round floats."""
    _checksum(checksum)
    values = []
    for component in checksum['components']:
        kind, value = component['type'], component['value']
        if kind in ('f32', 'f64'):
            value = struct.unpack('>f' if kind == 'f32' else '>d', bytes.fromhex(value[2:]))[0]
        elif kind != 'bool':
            value = int(value)
        values.append(value)
    return tuple(values)


def legacy_checksum(text, types):
    """Audited integer/bool line protocol; float cases need their own rule."""
    lines = text.splitlines()
    _require(len(lines) == len(types), 'legacy checksum component count')
    components = []
    for kind, line in zip(types, lines):
        if kind == 'bool':
            _require(line in ('true', 'false'), 'invalid legacy boolean')
            value = line == 'true'
        else:
            _require(kind in ('i8', 'u8', 'i16', 'u16', 'i32', 'u32', 'i64', 'u64'),
                     'legacy float/mixed output needs an audited case rule')
            value = line
        components.append(dict(type=kind, value=value))
    checksum = dict(components=components)
    _checksum(checksum)
    return decoded_checksum(checksum)


def measurement(report, *, key, size, types):
    """Project one validated row into the suite without discarding provenance."""
    _require(len(report['results']) == 1, 'expected one native row')
    row = report['results'][0]
    _require((row['key'], row['size']) == (key, size), 'unexpected native row')
    _require([c['type'] for c in row['checksum']['components']] == list(types), 'unexpected result types')
    return dict(ok=True, ms=1000 * row['summary']['median_seconds'],
                peak=row['process_peak_rss_bytes'], checksum=row['checksum'],
                statistic='median', timing_scope='function', isolation=row['isolation'],
                thermal_policy=report['policy']['thermal'], configuration_id=row['configuration_id'],
                key=key, size=size, native_report=report)


def shared_samples(report, *, key, size, units):
    """Map accepted native calls to the shared harness's distribution fields."""
    _require(type(units) is int and units > 0, 'invalid work units')
    value = measurement(report, key=key, size=size, types=('u64',))
    samples = []
    for attempt in report['results'][0]['attempts']:
        if attempt['phase'] != 'measure' or attempt['status'] != 'accepted':
            continue
        seconds = attempt['seconds']
        rss = attempt['process_peak_rss_bytes']
        samples.append(dict(seconds=seconds, units=units,
                            checksum=decoded_checksum(attempt['checksum'])[0],
                            units_per_second=units / seconds, ns_per_unit=seconds * 1e9 / units,
                            process_peak_rss_kib=None if rss is None else rss / 1024))
    return value, samples


def run_native(executable, source, output, *, key, size, types, cc, samples=7,
               warmups=2, isolation='process', definitions=(), native_flags=(),
               temperature='required', gate=60, ceiling=65, dry_run=False):
    """Run one file/key/size. Dry runs only return argv; never launch a child."""
    _require(samples >= 5 and warmups >= 1, 'minimum five samples and one warmup')
    _require(temperature in ('required', 'off'), 'invalid temperature policy')
    source, output = Path(source).resolve(), Path(output).resolve()
    argv = [str(executable), 'bench', str(source), '--filter', key, '--sizes', size,
            '--samples', str(samples), '--warmups', str(warmups), '--isolation', isolation,
            '--cc', str(cc), '-O2', '--temp-gate', str(gate), '--temp-ceiling', str(ceiling),
            '--json', str(output)]
    if temperature == 'off':
        argv += ['--temperature', 'off']
    for definition in definitions:
        argv += ['--define', definition]
    argv += list(native_flags)
    if dry_run:
        return argv
    output.parent.mkdir(parents=True, exist_ok=True)
    # Never mistake an earlier artifact for output from a failed command.
    output.unlink(missing_ok=True)
    result = subprocess.run(argv, capture_output=True, text=True)
    output.with_suffix(output.suffix + '.log').write_text(result.stdout + result.stderr, encoding='utf-8')
    _require(result.returncode == 0, 'native bench failed; see ' + str(output) + '.log')
    report = read_results(output, allow_ungated=temperature == 'off')
    policy = report['policy']
    _require((policy['samples'], policy['warmups'], policy['isolation']) ==
             (samples, warmups, isolation), 'unexpected sampling policy')
    thermal = policy['thermal']
    _require((thermal['mode'], thermal['gate_c'], thermal['ceiling_c']) ==
             ('disabled' if temperature == 'off' else 'required', gate, ceiling), 'unexpected thermal policy')
    _require(Path(report['source']['path']).resolve() == source, 'unexpected source')
    for item in report['source']['files']:
        _require(hashlib.sha256(Path(item['path']).read_bytes()).hexdigest() == item['sha256'], 'source changed')
    _require(Path(report['toolchain']['cc']['path']).resolve() == Path(cc).resolve(), 'unexpected compiler')
    _require(hashlib.sha256(Path(executable).read_bytes()).hexdigest() == report['toolchain']['goose']['sha256'], 'compiler changed')
    _require(hashlib.sha256(Path(cc).read_bytes()).hexdigest() == report['toolchain']['cc']['sha256'], 'C compiler changed')
    config = next(c for c in report['configurations'] if c['id'] == report['results'][0]['configuration_id'])
    expected_definitions = {'BENCH_SIZE': size}
    for definition in definitions:
        name, value = definition.split('=', 1)
        decoded = json.loads(value)
        expected_definitions[name] = str(decoded).lower() if type(decoded) is bool else str(decoded)
    actual_definitions = {d['name']: str(d['value']).lower() if d['type'] == 'bool' else str(d['value'])
                          for d in config['definitions']}
    _require(actual_definitions == expected_definitions, 'unexpected build definitions')
    _require(config['goose_flags'] == ['-O2', '--bounds-check=on', '--recursive-frame-check=on',
                                      '--backend=native', '--runtime=linked'], 'unexpected Goose flags')
    expected_native_flags = ['-O2', '-fno-lto', *native_flags, '-lm', '-pthread', '-ldl',
                             '--cc=' + str(Path(cc).resolve())]
    _require(config['native_flags'] == expected_native_flags, 'unexpected native flags')
    value = measurement(report, key=key, size=size, types=types)
    value['artifact'] = str(output)
    return value


def _require(condition, message):
    if not condition:
        raise InvalidResult(message)


def _checksum(value):
    _require(isinstance(value, dict) and isinstance(value.get('components'), list) and value['components'], 'missing checksum')
    for component in value['components']:
        kind, data = component.get('type'), component.get('value')
        if kind == 'bool':
            _require(type(data) is bool, 'invalid boolean checksum')
        elif kind in ('f32', 'f64'):
            width = 8 if kind == 'f32' else 16
            _require(isinstance(data, str) and re.fullmatch(r'0x[0-9a-f]{' + str(width) + '}', data), 'invalid float bits')
            number = struct.unpack('>f' if width == 8 else '>d', bytes.fromhex(data[2:]))[0]
            _require(math.isfinite(number), 'nonfinite checksum')
        else:
            _require(kind in ('i8', 'u8', 'i16', 'u16', 'i32', 'u32', 'i64', 'u64'), 'unknown checksum type')
            _require(isinstance(data, str) and re.fullmatch(r'0|-?[1-9][0-9]*', data), 'invalid integer checksum')
            bits = int(kind[1:])
            low, high = (0, (1 << bits) - 1) if kind[0] == 'u' else (-(1 << (bits - 1)), (1 << (bits - 1)) - 1)
            _require(low <= int(data) <= high, 'integer checksum overflow')


def read_results(path, *, allow_ungated=False, configuration_id=None, checksum=None):
    try:
        return _read_results(path, allow_ungated=allow_ungated,
                             configuration_id=configuration_id, checksum=checksum)
    except (KeyError, TypeError, AttributeError, OverflowError, ValueError) as error:
        raise InvalidResult(str(error)) from error


def _read_results(path, *, allow_ungated=False, configuration_id=None, checksum=None):
    """Return audited rows plus full provenance; reject failed/incomplete runs.

    ``configuration_id`` and ``checksum`` let the caller enforce its expected
    configuration and cross-language case result. Values remain typed strings
    or float bits; this adapter does not invent a legacy printed checksum.
    """
    with open(path, encoding='utf-8') as stream:
        report = json.load(stream, parse_constant=lambda value: (_ for _ in ()).throw(InvalidResult('nonfinite JSON')))
    _require(type(report.get('schema_version')) is int and report['schema_version'] == 1, 'unknown schema version')
    _require(report.get('status') == 'ok' and report.get('finished_at') and report.get('error') is None, 'incomplete or failed run')
    policy = report['policy']
    _require(type(policy['samples']) is int and policy['samples'] >= 5 and type(policy['warmups']) is int and policy['warmups'] >= 1, 'invalid requested counts')
    thermal = policy['thermal']
    _require(all(type(thermal[name]) in (int, float) and math.isfinite(thermal[name])
                 for name in ('gate_c', 'ceiling_c', 'poll_interval_ms')) and
             thermal['gate_c'] <= thermal['ceiling_c'] and thermal['poll_interval_ms'] > 0,
             'invalid thermal policy')
    _require(thermal['mode'] == 'required' or (allow_ungated and thermal['mode'] == 'disabled'), 'ungated results are not permitted')
    sensor_ids = {sensor['id'] for sensor in thermal['sensors']}
    _require(len(sensor_ids) == len(thermal['sensors']), 'duplicate sensors')
    if thermal['mode'] == 'required':
        _require(bool(thermal['sensors']), 'missing required sensors')
    configurations = {c['id']: c for c in report['configurations']}
    _require(len(configurations) == len(report['configurations']), 'duplicate configurations')
    _require(report['toolchain']['goose'] and report['toolchain']['cc'], 'missing toolchain provenance')
    for config in configurations.values():
        identity = {key: config[key] for key in ('size', 'definitions', 'goose_flags', 'native_flags')}
        identity.update(goose_sha256=report['toolchain']['goose']['sha256'],
                        cc_sha256=report['toolchain']['cc']['sha256'],
                        source_files=sorted(report['source']['files'], key=lambda source: source['path']))
        digest = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
        _require(digest == config['id'], 'configuration fingerprint mismatch')
    rows = report['results']
    _require(bool(rows), 'empty results')
    keys = set()
    for row in rows:
        _require(row['status'] == 'ok' and row['error'] is None and row['summary'] is not None, 'incomplete or failed row')
        identity = row['configuration_id']
        _require(identity in configurations and configurations[identity]['size'] == row['size'], 'unknown configuration')
        _require(configuration_id is None or identity == configuration_id, 'unexpected configuration')
        _require(row['isolation'] == policy['isolation'], 'isolation mismatch')
        rss = row['process_peak_rss_bytes']
        _require(rss is None or (type(rss) is int and rss >= 0), 'invalid process RSS')
        key = (identity, row['key'])
        _require(key not in keys, 'duplicate result row')
        keys.add(key)
        _checksum(row['checksum'])
        _require(checksum is None or row['checksum'] == checksum, 'unexpected checksum')
        children = {child['id']: child for child in row['children']}
        _require(bool(children) and len(children) == len(row['children']), 'missing or duplicate children')
        measured, warmups, rejected, retry = [], 0, 0, 0
        for index, attempt in enumerate(row['attempts'], 1):
            _require(attempt['index'] == index and attempt['phase'] in ('warmup', 'measure'), 'invalid attempt order')
            _require(attempt['status'] in ('accepted', 'thermal_rejected') and attempt['error'] is None, 'failed attempt')
            phase = 'warmup' if warmups < policy['warmups'] else 'measure'
            slot = warmups + 1 if phase == 'warmup' else len(measured) + 1
            _require(attempt['phase'] == phase and attempt['slot'] == slot and attempt['retry'] == retry, 'invalid sample slot or retry')
            _require(attempt['child_id'] in children, 'unknown child')
            _checksum(attempt['checksum'])
            _require(attempt['checksum'] == row['checksum'], 'checksum disagreement')
            elapsed = attempt['elapsed_ns']
            _require(isinstance(elapsed, str) and re.fullmatch(r'[1-9][0-9]*', elapsed), 'nonpositive duration')
            seconds = Fraction(int(elapsed), 1_000_000_000)
            _require(type(attempt['seconds']) in (int, float) and math.isfinite(attempt['seconds']) and math.isclose(attempt['seconds'], float(seconds), rel_tol=1e-14), 'inconsistent duration')
            if thermal['mode'] == 'required':
                _require(all(type(attempt[name]) in (int, float) and math.isfinite(attempt[name]) for name in
                             ('temperature_before_c', 'temperature_after_c', 'temperature_max_observed_c', 'temperature_max_poll_gap_ms')), 'missing thermal coverage')
                readings = attempt['temperature_reads']
                for sensor in sensor_ids:
                    offsets = [int(reading['offset_ns']) for reading in readings if reading['sensor_id'] == sensor]
                    _require(len(offsets) >= 2 and offsets[0] <= 0 and offsets[-1] >= int(elapsed), 'missing thermal brackets')
                _require(all(reading['sensor_id'] in sensor_ids and math.isfinite(reading['c']) for reading in readings), 'invalid thermal trace')
                _require(attempt['temperature_max_poll_gap_ms'] >= 0, 'negative thermal poll gap')
                _require(bool(readings) and max(reading['c'] for reading in readings) == attempt['temperature_max_observed_c'], 'incorrect thermal maximum')
                _require((attempt['status'] == 'thermal_rejected') == (attempt['temperature_max_observed_c'] > thermal['ceiling_c']), 'incorrect thermal classification')
            if attempt['status'] == 'thermal_rejected':
                rejected += 1
                retry += 1
                _require(retry <= policy['max_retries'], 'exhausted thermal retries')
            elif attempt['phase'] == 'warmup':
                warmups += 1
                retry = 0
            else:
                measured.append(seconds)
                retry = 0
        _require(warmups == policy['warmups'] == row['accepted_warmups'], 'incomplete warmups')
        _require(len(measured) == policy['samples'] == row['accepted_samples'], 'incomplete samples')
        _require(rejected == row['thermal_rejections'], 'incorrect rejection count')
        if thermal['mode'] == 'required':
            _require(row['temperature_max_observed_c'] == max(a['temperature_max_observed_c'] for a in row['attempts']), 'incorrect row temperature')
        center = median(measured)
        mad = median(abs(value - center) for value in measured)
        expected = dict(median_seconds=center, seconds_mad=mad, seconds_mad_percent=100 * mad / center,
                        seconds_min=min(measured), seconds_max=max(measured))
        for name, value in expected.items():
            _require(type(row['summary'][name]) in (int, float) and math.isfinite(row['summary'][name]) and math.isclose(row['summary'][name], float(value), rel_tol=1e-13), 'incorrect summary: ' + name)
        for child in row['children']:
            _require(child['exit_code'] == 0 and child['signal'] is None, 'unclean child exit')
    return report
