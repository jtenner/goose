"""Native-only example test helpers; no TinyCC/thread fallback."""
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent.parent


def run(argv, *, ok=True, timeout=120, env=None):
    p = subprocess.run(list(map(str, argv)), capture_output=True, text=True, timeout=timeout, env=env)
    assert (p.returncode == 0) == ok, (argv, p.returncode, p.stdout, p.stderr)
    return p


def build(goose, source, target, *flags):
    env = dict(os.environ, GOOSE_HOME=str(Path(target).parent / "goose-home"))
    run([goose, "build", *flags, source, "-o", target], timeout=600, env=env)
    return target
