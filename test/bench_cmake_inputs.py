#!/usr/bin/env python3
"""Selected CMake target dependency checks; no performance assertions."""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

exe = pathlib.Path(sys.argv.pop(1)).resolve()


class CMakeInputs(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='goose-cmake-inputs-')
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.env = dict(os.environ)
        self.source = self.root / 'entry.goose'
        self.source.write_text('extern fn value() -> i64;\nbench "input" fn entry() -> i64 { value() }\n')
        (self.root / 'entry.build').write_text('cmake_target = "value";\n')
        (self.root / 'value.c').write_text('#include <stdint.h>\n#ifdef UNRELATED\n'
                                         '#include "missing-generated.h"\n#endif\n'
                                         'int64_t dependency_value(void);\n'
                                         'int64_t value(void) { return dependency_value(); }\n')
        (self.root / 'dependency.c').write_text('#include <stdint.h>\n#include "dependency.h"\n'
                                              'int64_t dependency_value(void) { return VALUE; }\n')
        self.header = self.root / 'dependency.h'
        self.header.write_text('#define VALUE 42\n')
        self.cmake = self.root / 'CMakeLists.txt'
        self.base = ('cmake_minimum_required(VERSION 3.20)\nproject(value C)\n'
                     'add_library(dependency STATIC dependency.c)\n'
                     'add_library(value STATIC value.c)\n'
                     'target_link_libraries(value PRIVATE dependency)\n')
        self.cmake.write_text(self.base)
        self.report = self.root / 'report.json'

    def invoke(self):
        return subprocess.run([str(exe), 'bench', str(self.source), '--temperature', 'off',
                               '--samples', '5', '--warmups', '1', '--json', str(self.report)],
                              capture_output=True, text=True, timeout=120, env=self.env)

    def successful(self):
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(self.report.read_text())

    def test_excluded_generated_source(self):
        self.cmake.write_text(self.base +
            'add_custom_command(OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/unused.c\n'
            ' COMMAND ${CMAKE_COMMAND} -E copy ${CMAKE_CURRENT_SOURCE_DIR}/value.c ${CMAKE_CURRENT_BINARY_DIR}/unused.c)\n'
            'add_library(unused STATIC EXCLUDE_FROM_ALL ${CMAKE_CURRENT_BINARY_DIR}/unused.c)\n')
        report = self.successful()
        self.assertEqual(report['results'][0]['checksum']['components'][0]['value'], '42')
        self.assertFalse(any('unused.c' in flag for flag in report['configurations'][0]['native_flags']))

    def test_same_source_unrelated_flags(self):
        self.cmake.write_text(self.base + 'add_library(unrelated STATIC EXCLUDE_FROM_ALL value.c)\n'
                              'target_compile_definitions(unrelated PRIVATE UNRELATED=1)\n')
        report = self.successful()
        self.assertFalse(any('UNRELATED' in flag for flag in report['configurations'][0]['native_flags']))

    def test_transitive_object_dependency(self):
        self.cmake.write_text(self.base.replace('dependency STATIC', 'dependency OBJECT'))
        first = self.successful()
        files = {entry['path'] for entry in first['source']['files']}
        self.assertTrue({str(self.header), str(self.root / 'dependency.c')} <= files)
        self.header.write_text('#define VALUE 43\n')
        second = self.successful()
        self.assertNotEqual(first['configurations'][0]['id'], second['configurations'][0]['id'])
        self.assertEqual(second['results'][0]['checksum']['components'][0]['value'], '43')
        before = self.header.read_bytes()
        self.report = self.header
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('would overwrite an input', result.stdout + result.stderr)
        self.assertEqual(self.header.read_bytes(), before)

    def test_required_generated_source_still_rejected(self):
        self.cmake.write_text(self.base +
            'add_custom_command(OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/required.c\n'
            ' COMMAND ${CMAKE_COMMAND} -E copy ${CMAKE_CURRENT_SOURCE_DIR}/dependency.c ${CMAKE_CURRENT_BINARY_DIR}/required.c)\n'
            'target_sources(value PRIVATE ${CMAKE_CURRENT_BINARY_DIR}/required.c)\n')
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('cannot resolve native dependencies', result.stdout + result.stderr)
        self.assertFalse(self.report.exists())

    def test_absolute_subdirectory_build_path(self):
        subdir = self.root / 'dependency'
        subdir.mkdir()
        (subdir / 'CMakeLists.txt').write_text(
            'add_library(dependency STATIC ../dependency.c)\n')
        self.cmake.write_text(self.base.replace(
            'add_library(dependency STATIC dependency.c)',
            f'add_subdirectory(dependency "{self.root / "absolute-build"}")'))
        report = self.successful()
        self.assertEqual(report['results'][0]['checksum']['components'][0]['value'], '42')
        self.assertEqual(len([attempt for attempt in report['results'][0]['attempts']
                              if attempt['phase'] == 'measure']), 5)
        self.assertIn(str(self.header), {entry['path'] for entry in report['source']['files']})

    def test_timestamp_preserving_header_change(self):
        compiler = shutil.which('cc')
        count = self.root / 'compiles'
        wrapper = self.root / 'cc-wrapper'
        wrapper.write_text('#!/usr/bin/env python3\nimport os, sys\n'
                           'if "-c" in sys.argv and "-M" not in sys.argv and '
                           'any(x.endswith("/dependency.c") for x in sys.argv):\n'
                           f'    with open({str(count)!r}, "a") as out: out.write("compile\\n")\n'
                           f'os.execv({compiler!r}, [{compiler!r}, *sys.argv[1:]])\n')
        wrapper.chmod(0o755)
        self.env['GOOSE_CC'] = str(wrapper)
        first = self.successful()
        self.assertEqual(first['results'][0]['checksum']['components'][0]['value'], '42')
        self.assertEqual(count.read_text().splitlines(), ['compile'])
        self.successful()
        self.assertEqual(count.read_text().splitlines(), ['compile'])
        before = self.header.stat()
        self.header.write_text('#define VALUE 43\n')
        os.utime(self.header, ns=(before.st_atime_ns, before.st_mtime_ns))
        self.assertEqual(self.header.stat().st_mtime_ns, before.st_mtime_ns)
        second = self.successful()
        self.assertNotEqual(first['configurations'][0]['id'], second['configurations'][0]['id'])
        self.assertNotEqual(next(entry['sha256'] for entry in first['source']['files']
                                 if entry['path'] == str(self.header)),
                            next(entry['sha256'] for entry in second['source']['files']
                                 if entry['path'] == str(self.header)))
        self.assertEqual(second['results'][0]['checksum']['components'][0]['value'], '43')
        self.assertEqual(count.read_text().splitlines(), ['compile', 'compile'])

    def test_makefiles_without_output_field(self):
        # Exercise both supported generators and the optional compile database
        # output field without changing the host PATH or installed tools.
        tools = self.root / 'tools'
        tools.mkdir()
        cmake = shutil.which('cmake')
        wrapper = tools / 'cmake'
        wrapper.write_text(f'#!{sys.executable}\nimport json, pathlib, subprocess, sys\n'
                           'args = sys.argv[1:]\n'
                           'if "-S" in args:\n'
                           '    if "-G" in args: args[args.index("-G") + 1] = "Unix Makefiles"\n'
                           '    else: args += ["-G", "Unix Makefiles"]\n'
                           '    args = [a for a in args if not a.startswith("-DCMAKE_MAKE_PROGRAM=")]\n'
                           f'code = subprocess.call([{cmake!r}, *args])\n'
                           'if not code and "-S" in args:\n'
                           '    db = pathlib.Path(args[args.index("-B") + 1]) / "compile_commands.json"\n'
                           '    entries = json.loads(db.read_text())\n'
                           '    for entry in entries: entry.pop("output", None)\n'
                           '    db.write_text(json.dumps(entries))\n'
                           'sys.exit(code)\n')
        wrapper.chmod(0o755)
        self.env['PATH'] = str(tools) + os.pathsep + self.env['PATH']
        report = self.successful()
        db = next(pathlib.Path(entry['path']) for entry in report['source']['files']
                  if entry['path'].endswith('/compile_commands.json'))
        self.assertTrue(all('output' not in entry for entry in json.loads(db.read_text())))
        self.assertIn('CMAKE_GENERATOR:INTERNAL=Unix Makefiles', (db.parent / 'CMakeCache.txt').read_text())


if __name__ == '__main__':
    unittest.main()
