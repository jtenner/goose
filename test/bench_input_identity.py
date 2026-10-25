#!/usr/bin/env python3
"""Focused input safety and native identity checks; no performance assertions."""
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile

exe = pathlib.Path(sys.argv[1]).resolve()
checks = 0

with tempfile.TemporaryDirectory(prefix='goose-bench-inputs-') as directory:
    root = pathlib.Path(directory)
    source = root / 'entry.goose'
    header = root / 'value.h'
    native = root / 'value.c'
    sidecar = root / 'entry.build'
    source.write_text('extern fn value() -> i64;\nbench "input" fn entry() -> i64 { value() }\n')
    header.write_text('#include <stdint.h>\nstatic int64_t value(void) { return 42; }\n')
    native.write_text('#include <stdint.h>\nint64_t value(void) { return 42; }\n')
    sidecar.write_text('c_sources = ["value.c"];\n')

    def invoke(*options, ok=True):
        global checks
        result = subprocess.run([str(exe), 'bench', str(source), '--temperature', 'off',
                                 *map(str, options)], text=True, capture_output=True, timeout=120)
        assert (result.returncode == 0) == ok, (result.args, result.stdout, result.stderr)
        checks += 1
        return result

    # A failed build and --list must both preserve every known input.
    for listing in ([], ['--list']):
        for target in (header, sidecar, native):
            before = target.read_bytes()
            for option in ('--json', '--csv'):
                result = invoke(*listing, '--include', header, option, target, ok=False)
                assert 'would overwrite an input' in result.stdout + result.stderr, (result.stdout, result.stderr)
                assert target.read_bytes() == before
    # The derived samples CSV is an output too, including through a symlink.
    samples = root / 'value.samples.csv'
    samples.symlink_to(header)
    result = invoke('--list', '--include', header, '--csv', root / 'value.csv', ok=False)
    assert 'would overwrite an input' in result.stdout + result.stderr, (result.stdout, result.stderr)
    assert not (root / 'value.csv').exists()
    source.write_text('extern fn value() -> i64;\nbench "bad" fn entry() -> i64 { missing_name }\n')
    before = sidecar.read_bytes()
    invoke('--list', '--json', sidecar, ok=False)
    assert sidecar.read_bytes() == before
    # Protect an explicitly selected compiler even when parsing fails first.
    compiler_input = root / 'compiler-input'
    compiler_input.write_text('compiler bytes must survive\n')
    compiler_input.chmod(0o755)
    invoke('--list', '--cc', compiler_input, '--json', compiler_input, ok=False)
    assert compiler_input.read_text() == 'compiler bytes must survive\n'

    def report(*options):
        path = root / 'report.json'
        result = invoke('--samples', '5', '--warmups', '1', '--json', path, *options)
        data = json.loads(path.read_text())
        assert data['status'] == 'ok'
        for item in data['source']['files']:
            assert item['sha256'] == hashlib.sha256(pathlib.Path(item['path']).read_bytes()).hexdigest()
        return data, data['configurations'][0]['id']

    # The entry is deliberately tiny. These runs test identity and checksums,
    # never timing or performance. Paths include make-special characters.
    source.write_text('extern fn value() -> i64;\nbench "input" fn entry() -> i64 { value() }\n')
    sidecar.unlink()
    dependency = root / 'nested value$#.h'
    dependency.write_text('#define VALUE 42\n')
    header.write_text('#include <stdint.h>\n#include "nested value$#.h"\n'
                      'static int64_t value(void) { return VALUE; }\n')
    listing = root / 'listing.json'
    invoke('--list', '--include', header, '--json', listing)
    listing_id = json.loads(listing.read_text())['configurations'][0]['id']
    header.write_text(header.read_text() + '\n')
    invoke('--list', '--include', header, '--json', listing)
    assert json.loads(listing.read_text())['configurations'][0]['id'] != listing_id
    before = dependency.read_bytes()
    result = invoke('--include', header, '--json', dependency, ok=False)
    assert 'would overwrite an input' in result.stdout + result.stderr
    assert dependency.read_bytes() == before
    first, first_id = report('--include', header)
    repeat, repeat_id = report('--include', header)
    assert first_id == repeat_id
    assert {str(header), str(dependency)} <= {item['path'] for item in first['source']['files']}
    assert first['results'][0]['checksum']['components'][0]['value'] == '42'
    dependency.write_text('#define VALUE 43\n')
    changed, changed_id = report('--include', header)
    assert first_id != changed_id
    assert changed['results'][0]['checksum']['components'][0]['value'] == '43'

    # Sidecar source, transitive header, effective flags and linked object hashes.
    native.write_text('#include <stdint.h>\n#include "nested value$#.h"\n'
                      '#ifndef EXTRA\n#define EXTRA 0\n#endif\n'
                      'int64_t value(void) { return VALUE + EXTRA; }\n')
    sidecar.write_text('c_sources = ["value.c"];\nc_defines = ["EXTRA=1"];\n')
    first, first_id = report()
    assert first['results'][0]['checksum']['components'][0]['value'] == '44'
    assert any('native-compile=' in flag and '-DEXTRA=1' in flag
               for flag in first['configurations'][0]['native_flags'])
    assert any(item['path'].endswith('.o') and 'native' in item['path']
               for item in first['source']['files'])
    native_object = next(pathlib.Path(item['path']) for item in first['source']['files']
                         if item['path'].endswith('.o') and '/native/' in item['path'])
    before = native_object.read_bytes()
    saved = source.read_text()
    source.write_text('extern fn absent_symbol() -> i64;\n'
                      'bench "input" fn entry() -> i64 { absent_symbol() }\n')
    result = invoke('--json', native_object, ok=False)
    assert 'would overwrite an input' in result.stdout + result.stderr
    assert native_object.read_bytes() == before
    source.write_text(saved)
    dependency.write_text('#define VALUE 44\n')
    changed, changed_id = report()
    assert first_id != changed_id
    assert changed['results'][0]['checksum']['components'][0]['value'] == '45'
    sidecar.write_text('c_sources = ["value.c"];\nc_flags_cc = ["-DEXTRA=2"];\n')
    flags, flags_id = report()
    assert flags_id != changed_id
    assert flags['results'][0]['checksum']['components'][0]['value'] == '46'
    native.write_text(native.read_text().replace('VALUE + EXTRA', 'VALUE + EXTRA + 1'))
    changed, changed_id = report()
    assert changed_id != flags_id
    assert changed['results'][0]['checksum']['components'][0]['value'] == '47'

    response = root / 'flags.rsp'
    response.write_text('-DEXTRA=3\n')
    sidecar.write_text('c_sources = ["value.c"];\nc_flags_cc = ["@' + str(response) + '"];\n')
    invoke('--list', '--json', response, ok=False)
    assert response.read_text() == '-DEXTRA=3\n'
    first, first_id = report()
    assert first['results'][0]['checksum']['components'][0]['value'] == '48'
    response.write_text('-DEXTRA=4\n')
    changed, changed_id = report()
    assert changed_id != first_id
    assert changed['results'][0]['checksum']['components'][0]['value'] == '49'

    # Change a dependency after its snapshot, under a controlled compiler wrapper.
    import shutil
    compiler = shutil.which('cc')
    wrapper = root / 'cc-wrapper'
    wrapper.write_text('#!/usr/bin/env python3\nimport os, pathlib, sys\n'
                       f'header = pathlib.Path({str(dependency)!r})\n'
                       f'source = {str(native)!r}\n'
                       'if "-c" in sys.argv and source in sys.argv:\n'
                       '    header.write_text("#define VALUE 99\\n")\n'
                       f'os.execv({compiler!r}, [{compiler!r}, *sys.argv[1:]])\n')
    wrapper.chmod(0o755)
    # A source change makes the native build enter CompileObject.
    native.write_text(native.read_text() + '\n')
    result = invoke('--cc', wrapper, '--json', root / 'changed.json', ok=False)
    assert 'changed during build' in result.stdout + result.stderr, (result.stdout, result.stderr)
    assert json.loads((root / 'changed.json').read_text())['status'] == 'failed'

    # A linked object can change without any source or sidecar change.
    wrapper.write_text('#!/usr/bin/env python3\nimport os, pathlib, shlex, sys\n'
                       f'count = pathlib.Path({str(root / "links")!r})\n'
                       'if "-Wl,-t" in sys.argv:\n'
                       '    n = int(count.read_text()) + 1 if count.exists() else 1\n'
                       '    count.write_text(str(n))\n'
                       '    if n == 2:\n'
                       '        rsp = next(x[1:] for x in sys.argv if x.startswith("@"))\n'
                       '        obj = pathlib.Path(shlex.split(pathlib.Path(rsp).read_text())[0])\n'
                       '        obj.write_bytes(obj.read_bytes() + b"\\0")\n'
                       f'os.execv({compiler!r}, [{compiler!r}, *sys.argv[1:]])\n')
    result = invoke('--cc', wrapper, '--json', root / 'linked-change.json', ok=False)
    assert 'link input changed during build' in result.stdout + result.stderr, (result.stdout, result.stderr)

    wrapper.write_text('#!/usr/bin/env python3\nimport os, sys\n'
                       'if "-M" in sys.argv and any(x.endswith("/runner.c") for x in sys.argv):\n'
                       '    sys.exit(0)\n'
                       f'os.execv({compiler!r}, [{compiler!r}, *sys.argv[1:]])\n')
    path = root / 'missing-dependencies.json'
    result = invoke('--cc', wrapper, '--json', path, ok=False)
    assert 'cannot read provenance input' in result.stdout + result.stderr
    assert not path.exists()

    # CMake targets supply their actual compile flags and linked archive hashes.
    sidecar.write_text('cmake_target = "value";\n')
    cmake = root / 'CMakeLists.txt'
    cmake.write_text('cmake_minimum_required(VERSION 3.20)\nproject(value C)\n'
                     'add_library(value STATIC value.c)\n'
                     'target_compile_definitions(value PRIVATE EXTRA=5)\n')
    first, first_id = report()
    assert first['results'][0]['checksum']['components'][0]['value'] == '105'
    assert any(item['path'].endswith('.a') and 'libvalue' in item['path'] for item in first['source']['files'])
    assert any('native-compile=' in flag and '-DEXTRA=5' in flag for flag in first['configurations'][0]['native_flags'])
    cmake.write_text(cmake.read_text().replace('EXTRA=5', 'EXTRA=6'))
    changed, changed_id = report()
    assert first_id != changed_id
    assert changed['results'][0]['checksum']['components'][0]['value'] == '106'

print(f'benchmark input safety and identity: {checks} checks passed')
