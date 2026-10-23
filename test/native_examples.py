"""Register native example acceptance without TinyCC or timing workloads."""
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def register_acceptance(runner, goose, compiler, profile, *, capture, platform=sys.platform):
    if not platform.startswith('linux') or profile != 'baseline' or compiler is None or compiler.style != 'gcc':
        return 0
    suites = [('parallel_wasm.py', [goose, '--jobs', '64']),
              ('jit_clobbers.py', [goose]),
              ('conditional_shared_layout.py', [goose]),
              ('native_config_definitions.py', [goose]),
              ('shared_benchmark_harness.py', [])]
    for script, arguments in suites:
        def acceptance(script=script, arguments=arguments):
            try:
                code, out, err = capture([sys.executable, HERE / script, *arguments])
                if code:
                    runner.fail(script, out + err)
                else:
                    runner.ok(out.strip())
            except (OSError, subprocess.TimeoutExpired) as error:
                runner.fail(script, str(error))
        acceptance.__name__ = 'native_' + Path(script).stem
        runner.show_task(acceptance)
    return len(suites)
