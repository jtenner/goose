#!/usr/bin/env python3
"""Runner contract: native-only gating, short stress, and no benchmark execution."""
from pathlib import Path
from types import SimpleNamespace
from native_examples import register_acceptance


class Runner:
    def __init__(self):
        self.tasks, self.successes, self.failures = [], [], []
    def show_task(self, task):
        self.tasks.append(task)
    def ok(self, text):
        self.successes.append(text)
    def fail(self, title, text):
        self.failures.append((title, text))


def check(platform, profile, compiler, expected):
    runner, calls = Runner(), []
    def capture(argv):
        calls.append(list(map(str, argv)))
        return 0, "accepted\n", ""
    register_acceptance(runner, Path('/compiler/goose'), compiler, profile,
                        platform=platform, capture=capture)
    for task in runner.tasks:
        task()
    assert len(calls) == expected and len(runner.successes) == expected and not runner.failures
    return calls


native = SimpleNamespace(style='gcc', cc='/compiler/clang', name='clang')
for platform, profile, compiler in [('win32','baseline',native), ('darwin','baseline',native),
                                     ('linux','sanitize',native), ('linux','baseline',None),
                                     ('linux','baseline',SimpleNamespace(style='msvc'))]:
    check(platform, profile, compiler, 0)
calls = check('linux', 'baseline', native, 5)
by_script = {Path(argv[1]).name: argv for argv in calls}
assert set(by_script) == {'parallel_wasm.py', 'jit_clobbers.py', 'conditional_shared_layout.py',
                          'native_config_definitions.py', 'shared_benchmark_harness.py'}
expected_goose = str(Path('/compiler/goose'))
assert by_script['parallel_wasm.py'][2:] == [expected_goose, '--jobs', '64']
assert by_script['shared_benchmark_harness.py'][2:] == []
assert all('--run' not in argv and '--compile-only' not in argv for argv in calls)
assert all(expected_goose in argv for name, argv in by_script.items() if name != 'shared_benchmark_harness.py')
# A native-only build without TinyCC still registers all five suites; no jit
# argument exists in the API. Failure is surfaced rather than counted as pass.
r = Runner()
register_acceptance(r, Path('/compiler/goose'), native, 'baseline', platform='linux',
                    capture=lambda argv: (1, 'partial output', 'rejection detail'))
for task in r.tasks:
    task()
assert len(r.failures) == 5 and not r.successes
assert all('rejection detail' in detail for _, detail in r.failures)
print('native example runner integration contract passed')
