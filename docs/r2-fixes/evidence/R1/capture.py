#!/usr/bin/env python3
"""Save exact command, environment, output streams, and exit status."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent

def run(name, argv):
    out = HERE / (name + '.stdout')
    err = HERE / (name + '.stderr')
    with out.open('wb') as stdout, err.open('wb') as stderr:
        result = subprocess.run(argv, stdout=stdout, stderr=stderr)
    record = {'argv': [str(a) for a in argv], 'cwd': os.getcwd(),
              'environment': {key: os.environ.get(key) for key in
                              ('PATH', 'CC', 'CXX', 'CMAKE_BUILD_PARALLEL_LEVEL')},
              'exit_status': result.returncode,
              'stdout_sha256': hashlib.sha256(out.read_bytes()).hexdigest(),
              'stderr_sha256': hashlib.sha256(err.read_bytes()).hexdigest()}
    (HERE / (name + '.json')).write_text(json.dumps(record, indent=2) + '\n')
    print(f'{name}: exit {result.returncode}', flush=True)
    return result.returncode

if __name__ == '__main__':
    sys.exit(run(sys.argv[1], sys.argv[2:]))
