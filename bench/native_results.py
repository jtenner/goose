"""Read native Goose JSON v1 results without running or timing a workload.

The caller owns work units, cross-language checks, and experiment ordering.
Only complete rows with valid counts and policy can enter a comparison.
"""
import hashlib
import json
import math
import re
import struct
from fractions import Fraction
from statistics import median


class InvalidResult(ValueError):
    pass


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
    _require(thermal['mode'] == 'required' or (allow_ungated and thermal['mode'] == 'disabled'), 'ungated results are not permitted')
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
        key = (identity, row['key'])
        _require(key not in keys, 'duplicate result row')
        keys.add(key)
        _checksum(row['checksum'])
        _require(checksum is None or row['checksum'] == checksum, 'unexpected checksum')
        measured, warmups, rejected = [], 0, 0
        for index, attempt in enumerate(row['attempts'], 1):
            _require(attempt['index'] == index and attempt['phase'] in ('warmup', 'measure'), 'invalid attempt order')
            _require(attempt['status'] in ('accepted', 'thermal_rejected') and attempt['error'] is None, 'failed attempt')
            _checksum(attempt['checksum'])
            _require(attempt['checksum'] == row['checksum'], 'checksum disagreement')
            elapsed = attempt['elapsed_ns']
            _require(isinstance(elapsed, str) and re.fullmatch(r'[1-9][0-9]*', elapsed), 'nonpositive duration')
            seconds = Fraction(int(elapsed), 1_000_000_000)
            _require(type(attempt['seconds']) in (int, float) and math.isfinite(attempt['seconds']) and math.isclose(attempt['seconds'], float(seconds), rel_tol=1e-14), 'inconsistent duration')
            if attempt['status'] == 'thermal_rejected':
                rejected += 1
            elif attempt['phase'] == 'warmup':
                warmups += 1
            else:
                measured.append(seconds)
        _require(warmups == policy['warmups'] == row['accepted_warmups'], 'incomplete warmups')
        _require(len(measured) == policy['samples'] == row['accepted_samples'], 'incomplete samples')
        _require(rejected == row['thermal_rejections'], 'incorrect rejection count')
        center = median(measured)
        mad = median(abs(value - center) for value in measured)
        expected = dict(median_seconds=center, seconds_mad=mad, seconds_mad_percent=100 * mad / center,
                        seconds_min=min(measured), seconds_max=max(measured))
        for name, value in expected.items():
            _require(type(row['summary'][name]) in (int, float) and math.isfinite(row['summary'][name]) and math.isclose(row['summary'][name], float(value), rel_tol=1e-13), 'incorrect summary: ' + name)
        for child in row['children']:
            _require(child['exit_code'] == 0 and child['signal'] is None, 'unclean child exit')
    return report
