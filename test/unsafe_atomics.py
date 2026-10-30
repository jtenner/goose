"""Fork-only raw atomic order matrix, C emission and backend rejections."""
from pathlib import Path
import toolchain as tc


def check_unsafe_atomics(exe, base, cc=None, *, runtime=None, extra=()):
    base = (Path(base) / "unsafe-atomic-contract").resolve()
    base.mkdir(parents=True, exist_ok=True)
    orders = ["Relaxed", "Acquire", "Release", "AcqRel", "SeqCst"]

    def check(name, body, expected=None, flags=()):
        source = base / (name + ".goose")
        tc.write_text(source, 'fn main() { ' + body + '; }\n')
        code, out, err = tc.run_capture([exe, *flags, '--check', source])
        if (code == 0) != (expected is None) or (expected and expected not in out + err):
            raise RuntimeError(f'{name}: exit {code}\n{out}{err}')
        return source

    for width in ('u32', 'u64'):
        for order in orders:
            for op, values, bad in [('load', '', ('Release', 'AcqRel')),
                                    ('store', ', 1', ('Acquire', 'AcqRel')),
                                    ('fetch_add', ', 1', ())]:
                check(f'{width}-{op}-{order}',
                      f'unsafe_atomic_{op}<{width}>(8{values}, "{order}")',
                      f'invalid memory order for atomic {op}' if order in bad else None)
            for failure in orders:
                valid = failure == 'Relaxed' or (failure == 'Acquire' and order in ('Acquire', 'AcqRel', 'SeqCst')) or (failure == order == 'SeqCst')
                check(f'{width}-cas-{order}-{failure}',
                      f'unsafe_atomic_compare_exchange<{width}>(8, 0, 1, "{order}", "{failure}")',
                      None if valid else 'invalid compare_exchange failure order')
        for op, values in [('load', ', "Relaxed"'), ('store', ', 1, "Release"'),
                           ('fetch_add', ', 1, "AcqRel"'),
                           ('compare_exchange', ', 0, 1, "SeqCst", "Acquire"')]:
            source = check(f'emit-{width}-{op}', f'unsafe_atomic_{op}<{width}>(8{values})')
            cfile = source.with_suffix('.c')
            code, out, err = tc.run_capture([exe, '-O0', '-o', cfile, source])
            if code:
                raise RuntimeError(out + err)
            text = cfile.read_text()
            needle = '__atomic_' + {'load': 'load_n', 'store': 'store_n', 'fetch_add': 'fetch_add', 'compare_exchange': 'compare_exchange_n'}[op] + '('
            if needle not in text or 'unsafe atomic address is null, misaligned' not in text:
                raise RuntimeError(f'{source}: missing native operation or alignment diagnostic')
            body = text[text.index('/* ---- generated'): ] if '/* ---- generated' in text else text[text.index('_Static_assert(__atomic_always_lock_free'): ]
            if 'gs_shared_atomic_region(' in body or 'gs_shared_slabs[' in body:
                raise RuntimeError(f'{source}: raw operation unexpectedly uses shared registry')
            if op == 'compare_exchange' and ', 0, __ATOMIC_SEQ_CST, __ATOMIC_ACQUIRE)' not in text:
                raise RuntimeError('compare_exchange must be strong with validated orders')
            if cc and cc.style == 'gcc':
                for macro in ('__TINYC__', '_MSC_VER'):
                    code, out, err = tc.run_capture([cc.cc, '-E', '-D' + macro, cfile])
                    if code == 0 or 'Unsafe raw address atomics require GCC or Clang' not in err:
                        raise RuntimeError(f'{macro}: missing explicit backend rejection\n{out}{err}')
        if cc and cc.style == 'gcc':
            source = check(f'misaligned-{width}', f'unsafe_atomic_load<{width}>(1, "Relaxed")')
            cfile = source.with_suffix('.c')
            code, out, err = tc.run_capture([exe, '-o', cfile, source])
            if code:
                raise RuntimeError(out + err)
            binary = source.with_suffix(tc.EXE_SUFFIX or '.exe')
            ok, log = cc.compile(cfile, binary, runtime=runtime, extra=extra)
            if not ok:
                raise RuntimeError(log)
            code, out, err = tc.run_capture([binary])
            if code == 0 or 'unsafe atomic address is null, misaligned' not in err or tc.sanitizer_failure(err):
                raise RuntimeError('misaligned address did not abort loudly\n' + out + err)
        if cc and cc.style == 'gcc':
            # Force the target query false to exercise the compile-time rejection.
            unsupported = base / f'unsupported-{width}.c'
            tc.write_text(unsupported, text.replace('_Static_assert(__atomic_always_lock_free(' + ('4' if width == 'u32' else '8') + ', 0)', '_Static_assert(0', 1))
            code, out, err = tc.run_capture([cc.cc, '-fsyntax-only', unsupported])
            if code == 0 or 'Unsafe raw atomic width is not always lock-free' not in err:
                raise RuntimeError('missing non-lock-free width rejection\n' + out + err)
        check(f'{width}-no-type', 'unsafe_atomic_load(8, "Relaxed")', 'exactly one type argument')
        check(f'{width}-address-type', f'unsafe_atomic_load<{width}>(true, "Relaxed")', 'u64')
    # Integer addresses must not bypass the opt-in worker unsafe restriction.
    source = base / 'strict.goose'
    tc.write_text(source, 'thread_fn worker(a: u64) { unsafe_atomic_fetch_add<u64>(a, 1, "Relaxed"); } fn main() { thread_wait(thread_spawn(worker, 8)); }')
    code, out, err = tc.run_capture([exe, '--strict-worker-native', '--check', source])
    if code == 0 or 'unsafe native operation unsafe_atomic_fetch_add' not in err:
        raise RuntimeError('strict worker contract did not reject raw atomic\n' + out + err)
