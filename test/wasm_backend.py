#!/usr/bin/env python3
"""Differential tests for the direct Wasm backend; no generated-C Wasm path."""
import argparse
import random
import math
import struct
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(command, *, ok=True, timeout=90):
    try:
        result = subprocess.run([str(c) for c in command], cwd=ROOT, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        raise AssertionError(f"command exceeded {timeout}s test limit: {' '.join(map(str, command))}\n"
                             f"stderr:\n{(error.stderr or b'').decode(errors='replace')}") from error
    if ok and result.returncode:
        raise AssertionError(f"command failed ({result.returncode}): {' '.join(map(str, command))}\n"
                             f"stdout:\n{result.stdout.decode(errors='replace')}\n"
                             f"stderr:\n{result.stderr.decode(errors='replace')}")
    return result



def function_local_counts(data):
    def read(pos):
        value = shift = 0
        while True:
            byte = data[pos]; pos += 1
            value |= (byte & 127) << shift
            if not byte & 128:
                return value, pos
            shift += 7
    assert data[:8] == b'\0asm\x01\0\0\0'
    cursor, totals = 8, []
    while cursor < len(data):
        ident = data[cursor]; length, cursor = read(cursor + 1); end = cursor + length
        if ident == 10:
            count, cursor = read(cursor)
            for _ in range(count):
                length, cursor = read(cursor); body_end = cursor + length
                groups, cursor = read(cursor); total = 0
                for _ in range(groups):
                    amount, cursor = read(cursor); total += amount; cursor += 1
                assert cursor <= body_end
                totals.append(total); cursor = body_end
        cursor = end
    return totals


def main():
    from wasm_array_copy_admission import CASES as COPY_ADMISSION_CASES, reason as copy_admission_reason

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe', type=Path, default=ROOT / 'build' / 'goose')
    p.add_argument('--node', default='node')
    p.add_argument('--validator', default='wasm-tools')
    p.add_argument('--cc', default='cc')
    p.add_argument('--cxx', default='c++')
    p.add_argument('--shader-library', type=Path, default=ROOT / 'build' / 'libgoose_shaderc.a',
                   help='normal compiler shader library needed by the array-place test helper')
    p.add_argument('--out', type=Path, default=ROOT / 'build' / 'gen' / 'wasm')
    p.add_argument('--wasmtime-python', type=Path, help='Python with optional wasmtime==49.0.0')
    p.add_argument('--correctness-only', action='store_true',
                   help='run behavior, safety and memory-image checks without cost-only scaling reports')
    args = p.parse_args()
    exe = args.exe.resolve()
    for command in (args.node, args.validator, args.cc, args.cxx):
        if not shutil.which(command):
            p.error(f'required executable is missing: {command}')
        run([command, '--version'])  # Check broken version-manager shims too.
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    count = 0
    # Exercise the production data-memory helpers independently of AST
    # lowering, including genuine memory.grow failure under a hard limit.
    memory_exe, memory_wasm = out / 'memory-runtime', out / 'memory-runtime.wasm'
    limited_memory = out / 'memory-runtime-limited.wasm'
    run([args.cxx, '-std=c++20', '-O2', ROOT / 'test' / 'wasm_memory.cpp', '-o', memory_exe])
    run([memory_exe, memory_wasm])
    run([args.validator, 'validate', memory_wasm])
    run([args.node, ROOT / 'test' / 'wasm_memory.mjs', memory_wasm, limited_memory])
    run([args.validator, 'validate', limited_memory])
    count += 1
    if args.wasmtime_python:
        run([args.wasmtime_python, ROOT / 'test' / 'wasm_memory.py', memory_wasm, limited_memory])
        count += 1
    copy_matrix = out / 'memory-copy-matrix.wasm'
    run([memory_exe, copy_matrix, '65'])
    run([args.validator, 'validate', copy_matrix])
    run([args.node, ROOT / 'test' / 'wasm_copy_matrix.mjs', copy_matrix])
    count += 1
    if args.wasmtime_python:
        run([args.wasmtime_python, ROOT / 'test' / 'wasm_copy_matrix.py', copy_matrix])
        count += 1
    # Exercise private place forms before widening source-language admission.
    # The real AST pass definitions use the normal compiler shader library.
    shader_library = args.shader_library.resolve()
    if not shader_library.is_file():
        p.error(f'array-place test requires the compiler shader library: {shader_library}')
    places_exe, places_wasm = out / 'array-places', out / 'array-places.wasm'
    run([args.cxx, '-std=c++20', '-O0', ROOT / 'test' / 'wasm_array_places.cpp',
         shader_library, '-lm', '-pthread', '-ldl', '-o', places_exe], timeout=180)
    run([places_exe, places_wasm])
    run([args.validator, 'validate', places_wasm])
    run([args.node, ROOT / 'test' / 'wasm_array_places.mjs', places_wasm])
    count += 1
    if args.wasmtime_python:
        run([args.wasmtime_python, ROOT / 'test' / 'wasm_array_places.py', places_wasm])
        count += 1
    fixed_layout = out / 'fixed-layout'
    run([args.cxx, '-std=c++20', '-O2', ROOT / 'test' / 'wasm_fixed_layout.cpp', '-o', fixed_layout])
    run([fixed_layout])
    count += 1
    sources = sorted((ROOT / 'test' / 'wasm').glob('*.goose'))
    sources.extend(ROOT / 'test' / 'typing' / f'{name}.goose' for name in (
        'global_optional_flow', 'optional_loop_callee_assignments',
        'optional_while_condition_calls', 'u64_cmp_readonly_refs',
    ))
    for source in sources:
        expected = (ROOT / 'test' / 'expected' / (source.stem + '.out')).read_bytes()
        for opt in (0, 2):
            prefix = out / f'{source.stem}-O{opt}'
            c = prefix.with_suffix('.c')
            native = prefix.with_suffix('.native')
            wasm = prefix.with_suffix('.wasm')
            run([exe, f'-O{opt}', '--standalone', '-o', c, source])
            run([args.cc, f'-O{opt}', c, '-pthread', '-lm', '-ldl', '-o', native])
            reference = run([native])
            assert reference.stdout == expected, (source, opt, 'native fixture expectation')
            run([exe, f'-O{opt}', '--target', 'wasm', '-o', wasm, source])
            assert wasm.read_bytes()[:8] == b'\0asm\x01\0\0\0', 'invalid binary magic/version'
            run([args.validator, 'validate', wasm])
            if source.stem.startswith((
                    'wasm_inline_ref_abi_', 'wasm_data_aggregate_', 'wasm_constructor_assignment_',
                    'wasm_aggregate_construction_', 'wasm_array_assignment_', 'wasm_default_conversion_',
                    'wasm_array_constructor_', 'wasm_fixed_argument_', 'wasm_fixed_result_', 'wasm_array_argument_', 'wasm_array_result_', 'wasm_temporary_read_', 'wasm_temporary_equality_', 'wasm_fixed_negation_', 'wasm_fixed_binary_', 'wasm_compound_math_', 'wasm_negation_discard_')):
                actual = run([args.node, ROOT / 'test' / 'wasm_reference_abi.mjs', wasm,
                              out / f'{source.stem}-O{opt}-instance'])
            else:
                actual = run([args.node, ROOT / 'scripts' / 'run_wasm.mjs', wasm])
            assert actual.stdout == reference.stdout, (source, opt, actual.stdout, reference.stdout)
            assert not actual.stderr, (source, opt, actual.stderr)
            if args.wasmtime_python:
                second = run([args.wasmtime_python, ROOT / 'test' / 'wasmtime_host.py', wasm])
                assert second.stdout == reference.stdout and not second.stderr, (source, opt, second.stdout, second.stderr)
                count += 1
            if source.stem == 'wasm_tail_values':
                resource = run([args.node, ROOT / 'test' / 'wasm_runtime.mjs', wasm, 'print'])
                assert resource.stdout == reference.stdout, 'print owner check changed output'
                count += 1
            if source.stem in ('wasm_multimemory', 'wasm_scoped_data_reuse', 'wasm_array_widths',
                               'wasm_array_shrink', 'wasm_no_data_owner', 'wasm_entry_stack_base',
                               'wasm_ordered_array_cleanup', 'wasm_inline_arrays',
                               'wasm_inline_mixed_references', 'wasm_inline_reference_path',
                               'wasm_inline_limited_path', 'wasm_inline_effect_path',
                               'wasm_inline_nested_path', 'wasm_inline_boundaries',
                               'wasm_inline_optional_references', 'wasm_array_equality',
                               'wasm_inline_equality_modes', 'wasm_inline_deferred_rebind',
                               'wasm_variable_arrays', 'wasm_variable_paths', 'wasm_variable_no_owner',
                               'wasm_array_fills', 'wasm_variable_cleanup',
                               'wasm_byte_strings', 'wasm_byte_print', 'wasm_runtime_limited',
                               'wasm_runtime_limited_bytes', 'wasm_runtime_limited_cleanup',
                               'wasm_runtime_limited_no_owner', 'wasm_array_copy',
                               'wasm_array_copy_inline', 'wasm_array_copy_cleanup',
                               'wasm_array_copy_sources', 'wasm_varint_prefix',
                               'wasm_varint_paths', 'wasm_varint_bytes', 'wasm_varint_cleanup',
                               'wasm_struct_values', 'wasm_struct_arrays', 'wasm_struct_calls',
                               'wasm_struct_effects', 'wasm_struct_refs', 'wasm_struct_cleanup',
                               'wasm_struct_hidden', 'wasm_struct_review_fields_thin',
                               'wasm_struct_review_fields_packed', 'wasm_struct_review_calls_thin',
                               'wasm_struct_review_calls_packed', 'wasm_struct_review_reference_fields',
                               'wasm_struct_review_inline_only', 'wasm_struct_review_callback_only'):
                if source.stem == 'wasm_inline_arrays':
                    assert wasm.stat().st_size < 32768, 'unused global capacity was serialized'
                persistent = ('2' if source.stem in ('wasm_array_copy_sources', 'wasm_struct_review_reference_fields') else
                              '1' if source.stem in ('wasm_multimemory', 'wasm_variable_arrays', 'wasm_array_fills', 'wasm_byte_strings', 'wasm_runtime_limited', 'wasm_runtime_limited_bytes', 'wasm_array_copy', 'wasm_varint_prefix') else '0')
                mode = {'wasm_multimemory': 'growth', 'wasm_scoped_data_reuse': 'reuse',
                        'wasm_array_widths': 'typed-reuse', 'wasm_no_data_owner': 'no-data',
                        'wasm_inline_arrays': 'no-data', 'wasm_inline_reference_path': 'no-data',
                        'wasm_inline_limited_path': 'no-data', 'wasm_inline_effect_path': 'no-data',
                        'wasm_inline_nested_path': 'no-data', 'wasm_inline_boundaries': 'no-data',
                        'wasm_inline_equality_modes': 'no-data', 'wasm_variable_no_owner': 'no-data',
                        'wasm_variable_paths': 'variable-reuse',
                        'wasm_array_fills': 'variable-growth',
                        'wasm_byte_strings': 'variable-growth',
                        'wasm_byte_print': 'variable-growth',
                        'wasm_runtime_limited': 'variable-reuse',
                        'wasm_runtime_limited_bytes': 'variable-growth',
                        'wasm_runtime_limited_no_owner': 'no-data',
                        'wasm_array_copy': 'growth',
                        'wasm_array_copy_inline': 'no-data',
                        'wasm_varint_prefix': 'varint-prefix',
                        'wasm_varint_bytes': 'growth',
                        'wasm_struct_values': 'no-data', 'wasm_struct_arrays': 'no-data',
                        'wasm_struct_calls': 'no-data', 'wasm_struct_effects': 'no-data',
                        'wasm_struct_hidden': 'no-data', 'wasm_struct_cleanup': 'frame-growth',
                        'wasm_struct_review_fields_thin': 'no-data',
                        'wasm_struct_review_calls_thin': 'no-data',
                        'wasm_struct_review_inline_only': 'no-data',
                        'wasm_struct_review_callback_only': 'no-data'}.get(source.stem, '')
                resource = run([args.node, ROOT / 'test' / 'wasm_multimemory.mjs', wasm, persistent, mode])
                assert resource.stdout == reference.stdout, 'completed owner-state check changed output'
                count += 1
            if source.stem.startswith(('wasm_enum_', 'wasm_callback_', 'wasm_aggregate_array_', 'wasm_aggregate_iteration_')):
                mode = ('frame-growth' if source.stem in ('wasm_enum_cleanup', 'wasm_aggregate_array_cleanup',
                                                         'wasm_aggregate_iteration_cleanup') else
                        '' if source.stem in ('wasm_enum_containers', 'wasm_aggregate_array_packed',
                                             'wasm_aggregate_array_walk_packed', 'wasm_aggregate_array_nested_fields',
                                             'wasm_aggregate_array_callbacks', 'wasm_aggregate_iteration_refs_packed',
                                             'wasm_aggregate_iteration_walk_packed', 'wasm_aggregate_iteration_checkpoint') else 'no-data')
                resource = run([args.node, ROOT / 'test/wasm_multimemory.mjs', wasm, '0', mode])
                assert resource.stdout == reference.stdout, 'completed enum/callback owner-state check changed output'
                count += 1
            if source.stem.startswith('wasm_data_aggregate_'):
                persistent = '1' if source.stem in ('wasm_data_aggregate_enums', 'wasm_data_aggregate_overflow') else '0'
                checked = run([args.node, ROOT / 'test/wasm_multimemory.mjs', wasm, persistent])
                assert checked.stdout == reference.stdout and not checked.stderr
                count += 1
            if source.stem.startswith('wasm_field_iteration_'):
                mode = ('no-data' if source.stem in ('wasm_field_iteration_fixed', 'wasm_field_iteration_root',
                                                    'wasm_field_iteration_refs', 'wasm_field_iteration_zero',
                                                    'wasm_field_iteration_call', 'wasm_field_iteration_variant') else '')
                checked = run([args.node, ROOT / 'test/wasm_multimemory.mjs', wasm, '0', mode])
                assert checked.stdout == reference.stdout and not checked.stderr
                count += 1
            if source.stem.startswith(('wasm_compound_math_', 'wasm_negation_discard_')):
                mode = '' if source.stem in ('wasm_compound_math_data', 'wasm_compound_math_index_effect', 'wasm_compound_math_data_owner', 'wasm_compound_math_function_data') else 'no-data'
                checked = run([args.node, ROOT / 'test/wasm_multimemory.mjs', wasm, '1' if source.stem == 'wasm_compound_math_index_effect' else '0', mode])
                assert checked.stdout == reference.stdout and not checked.stderr
                count += 1
            if source.stem.startswith('wasm_fixed_binary_'):
                mode = '' if source.stem in ('wasm_fixed_binary_data', 'wasm_fixed_binary_index_effect',
                                            'wasm_fixed_binary_data_owner', 'wasm_fixed_binary_nested_destination',
                                            'wasm_fixed_binary_function_data') else 'no-data'
                checked = run([args.node, ROOT / 'test/wasm_multimemory.mjs', wasm, '0', mode])
                assert checked.stdout == reference.stdout and not checked.stderr
                count += 1
            if source.stem.startswith('wasm_fixed_negation_'):
                mode = '' if source.stem in ('wasm_fixed_negation_data', 'wasm_fixed_negation_data_owner', 'wasm_fixed_negation_field',
                                                             'wasm_fixed_negation_adapt_data', 'wasm_fixed_negation_adapt_data_owner',
                                                             'wasm_fixed_negation_adapt_function_data',
                                                             'wasm_fixed_negation_adapt_field_assignment_data') else 'no-data'
                checked = run([args.node, ROOT / 'test/wasm_multimemory.mjs', wasm, '0', mode])
                assert checked.stdout == reference.stdout and not checked.stderr
                count += 1
            if source.stem.startswith('wasm_temporary_equality_'):
                mode = '' if source.stem == 'wasm_temporary_equality_refs' else 'no-data'
                checked = run([args.node, ROOT / 'test/wasm_multimemory.mjs', wasm, '0', mode])
                assert checked.stdout == reference.stdout and not checked.stderr
                count += 1
            if source.stem.startswith('wasm_temporary_read_'):
                mode = '' if source.stem in ('wasm_temporary_read_mixed_fields', 'wasm_temporary_read_ref_compare', 'wasm_temporary_read_array_ref_identity') else 'no-data'
                checked = run([args.node, ROOT / 'test/wasm_multimemory.mjs', wasm, '0', mode])
                assert checked.stdout == reference.stdout and not checked.stderr
                count += 1
            if source.stem.startswith('wasm_array_result_'):
                mode = '' if source.stem in ('wasm_array_result_data', 'wasm_array_result_data_control', 'wasm_array_result_refs',
                                              'wasm_array_result_dynamic_base') else 'no-data'
                checked = run([args.node, ROOT / 'test/wasm_multimemory.mjs', wasm, '0', mode])
                assert checked.stdout == reference.stdout and not checked.stderr
                count += 1
            if source.stem.startswith('wasm_array_argument_'):
                mode = '' if source.stem in ('wasm_array_argument_data', 'wasm_array_argument_dynamic_base',
                                                   'wasm_array_argument_dynamic_source', 'wasm_array_argument_packed_refs') else 'no-data'
                checked = run([args.node, ROOT / 'test/wasm_multimemory.mjs', wasm, '0', mode])
                assert checked.stdout == reference.stdout and not checked.stderr
                count += 1
            if source.stem.startswith('wasm_fixed_result_'):
                mode = '' if source.stem in ('wasm_fixed_result_data', 'wasm_fixed_result_refs',
                                              'wasm_fixed_result_dynamic_base') else 'no-data'
                checked = run([args.node, ROOT / 'test/wasm_multimemory.mjs', wasm, '0', mode])
                assert checked.stdout == reference.stdout and not checked.stderr
                count += 1
            if source.stem.startswith('wasm_fixed_argument_'):
                mode = '' if source.stem in ('wasm_fixed_argument_data_field', 'wasm_fixed_argument_refs',
                                              'wasm_fixed_argument_reference_result',
                                              'wasm_fixed_argument_data_callback',
                                              'wasm_fixed_argument_dynamic_base') else 'no-data'
                checked = run([args.node, ROOT / 'test/wasm_multimemory.mjs', wasm, '0', mode])
                assert checked.stdout == reference.stdout and not checked.stderr
                count += 1
            if source.stem.startswith('wasm_array_constructor_'):
                mode = '' if source.stem in ('wasm_array_constructor_field', 'wasm_array_constructor_refs') else 'no-data'
                checked = run([args.node, ROOT / 'test/wasm_multimemory.mjs', wasm, '0', mode])
                assert checked.stdout == reference.stdout and not checked.stderr
                count += 1
            if source.stem.startswith('wasm_default_conversion_'):
                mode = '' if source.stem == 'wasm_default_conversion_data' else 'no-data'
                checked = run([args.node, ROOT / 'test/wasm_multimemory.mjs', wasm, '0', mode])
                assert checked.stdout == reference.stdout and not checked.stderr
                count += 1
            if source.stem.startswith('wasm_array_assignment_'):
                mode = '' if source.stem in ('wasm_array_assignment_data',
                                              'wasm_array_assignment_fat_order',
                                              'wasm_array_assignment_fat_refs',
                                              'wasm_array_assignment_nominal_refs',
                                              'wasm_array_assignment_field_carry') else 'no-data'
                checked = run([args.node, ROOT / 'test/wasm_multimemory.mjs', wasm, '0', mode])
                assert checked.stdout == reference.stdout and not checked.stderr
                count += 1
            if source.stem.startswith('wasm_aggregate_construction_'):
                mode = '' if source.stem in ('wasm_aggregate_construction_refs',
                                              'wasm_aggregate_construction_data_fields',
                                              'wasm_aggregate_construction_call_spans') else 'no-data'
                checked = run([args.node, ROOT / 'test/wasm_multimemory.mjs', wasm, '0', mode])
                assert checked.stdout == reference.stdout and not checked.stderr
                count += 1
            if source.stem.startswith('wasm_constructor_assignment_'):
                mode = '' if source.stem in ('wasm_constructor_assignment_targets',
                                              'wasm_constructor_assignment_order',
                                              'wasm_constructor_assignment_data_exit') else 'no-data'
                checked = run([args.node, ROOT / 'test/wasm_multimemory.mjs', wasm, '0', mode])
                assert checked.stdout == reference.stdout and not checked.stderr
                count += 1
            if source.stem.startswith('wasm_fixed_assignment_'):
                mode = ('' if source.stem in ('wasm_fixed_assignment_data', 'wasm_fixed_assignment_refs',
                                             'wasm_fixed_assignment_opaque', 'wasm_fixed_assignment_order',
                                             'wasm_fixed_assignment_lifetime') else 'no-data')
                checked = run([args.node, ROOT / 'test/wasm_multimemory.mjs', wasm, '0', mode])
                assert checked.stdout == reference.stdout and not checked.stderr
                count += 1
            if source.stem == 'wasm_byte_print':
                checked = run([args.node, ROOT / 'test' / 'wasm_bytes.mjs', wasm])
                assert checked.stdout == reference.stdout
                for control, reason in [('missing-drop', b'unreleased byte snapshot at owner completion'),
                                        ('alias-snapshot', b'byte argument was not captured before later effects')]:
                    broken = run([args.node, ROOT / 'test' / 'wasm_bytes.mjs', wasm, control], ok=False)
                    assert broken.returncode and reason in broken.stderr, (control, broken.stderr)
                    count += 1
                count += 1
            count += 1
    from wasm_struct_checks import check_modules as check_struct_modules, check_constructor_locals
    count += check_struct_modules(run, args.node, args.validator, args.wasmtime_python, out)
    from wasm_struct_admission import check_admission as check_struct_admission
    count += check_struct_admission(run, exe, args.node, args.validator, args.wasmtime_python, out)
    if not args.correctness_only:
        count += check_constructor_locals(run, exe, args.node, args.validator, args.wasmtime_python, out, function_local_counts)
    from wasm_enum_checks import check_modules as check_enum_modules, check_footprint as check_enum_footprint
    from wasm_enum_admission import check_admission as check_enum_admission
    count += check_enum_modules(run, args.node, args.validator, args.wasmtime_python, out)
    count += check_enum_admission(run, exe, args.cc, out, args.node, args.validator, args.wasmtime_python)
    if not args.correctness_only:
        count += check_enum_footprint(run, exe, args.node, args.validator, args.wasmtime_python, out, function_local_counts)
    from wasm_aggregate_checks import check_controls as check_aggregate_controls, check_reference_abi, check_footprint as check_aggregate_footprint
    from wasm_aggregate_admission import check_admission as check_aggregate_admission, check_limits as check_aggregate_limits
    count += check_aggregate_controls(run, args.node, args.validator, args.wasmtime_python, out)
    count += check_reference_abi(run, args.validator, out)
    count += check_aggregate_admission(run, exe, args.cc, out, args.node, args.validator, args.wasmtime_python)
    count += check_aggregate_limits(run, exe, out)
    if not args.correctness_only:
        count += check_aggregate_footprint(run, exe, args.node, args.validator, args.wasmtime_python, out, function_local_counts)
    from wasm_iteration_checks import check_modules as check_iteration_modules, check_limits as check_iteration_limits, check_footprint as check_iteration_footprint
    count += check_iteration_modules(run, args.node, args.validator, args.wasmtime_python, out)
    count += check_iteration_limits(run, exe, out)
    if not args.correctness_only:
        count += check_iteration_footprint(run, exe, args.cc, args.node, args.validator, args.wasmtime_python, out)
    owner_module = out / 'wasm_inline_ref_abi_packed-O0.wasm'
    owner_controls = out / 'reference-owner-controls'
    run([sys.executable, ROOT / 'test/wasm_reference_abi_controls.py', owner_module, owner_controls])
    for kind in ('print-owner', 'snapshot-owner'):
        run([args.validator, 'validate', owner_controls / f'{kind}.wasm'])
    run([args.node, ROOT / 'test/wasm_reference_abi_controls.mjs', owner_module, owner_controls,
         ROOT / 'test/expected/wasm_inline_ref_abi_packed.out', out / 'reference-owner-results.json'])
    count += 3
    from wasm_data_aggregate_checks import check_footprint as check_data_footprint, check_controls as check_data_controls
    if not args.correctness_only:
        count += check_data_footprint(run, exe, args.cc, args.node, args.validator, args.wasmtime_python, out, function_local_counts)
    count += check_data_controls(run, exe, args.cc, args.node, args.validator, args.wasmtime_python, out)
    from wasm_data_aggregate_named import check_named_footprint
    if not args.correctness_only:
        count += check_named_footprint(run, exe, args.cc, args.node, args.validator, args.wasmtime_python, out, function_local_counts)
    run([args.node, ROOT / 'test/wasm_memory_snapshot_checks.mjs'])
    count += 2
    from wasm_data_iteration_checks import check_modules as check_data_iteration_modules, check_recursion as check_data_iteration_recursion
    from wasm_data_iteration_admission import check_admission as check_data_iteration_admission
    from wasm_data_iteration_footprint import check_footprint as check_data_iteration_footprint
    count += check_data_iteration_modules(run, args.node, args.validator, args.wasmtime_python, out)
    count += check_data_iteration_recursion(run, args.node, args.validator, args.wasmtime_python, out)
    count += check_data_iteration_admission(run, exe, out, args.node, args.validator, args.wasmtime_python)
    from wasm_field_iteration_checks import check_paths as check_field_iteration_paths
    count += check_field_iteration_paths(run, exe, args.cc, args.node, args.validator, args.wasmtime_python, out)
    from wasm_fixed_assignment_checks import check_images as check_fixed_assignment_images, check_guards as check_fixed_assignment_guards
    count += check_fixed_assignment_images(run, args.node, args.validator, out)
    count += check_fixed_assignment_guards(run, exe, out, args.node, args.validator, args.wasmtime_python)
    from wasm_constructor_assignment_checks import check_owners as check_constructor_owners
    count += check_constructor_owners(run, args.node, args.validator, out)
    from wasm_constructor_assignment_checks import check_failure as check_constructor_failure
    count += check_constructor_failure(run, exe, args.cc, args.node, args.validator, out)
    from wasm_constructor_assignment_checks import check_target_failure as check_constructor_target_failure
    count += check_constructor_target_failure(run, exe, args.cc, args.node, args.validator, out)
    from wasm_aggregate_construction_checks import check_modules as check_aggregate_construction
    count += check_aggregate_construction(run, args.node, args.validator, out)
    from wasm_array_assignment_checks import check_images as check_array_assignment_images, check_references as check_array_assignment_references, check_guards as check_array_assignment_guards
    count += check_array_assignment_images(run, args.node, args.validator, out)
    count += check_array_assignment_references(run, args.node, args.validator, args.wasmtime_python, out)
    count += check_array_assignment_guards(run, exe, args.cc, args.node, out)
    from wasm_array_constructor_checks import check_owners as check_array_constructor_owners, check_failures as check_array_constructor_failures
    count += check_array_constructor_owners(run, args.node, args.validator, out)
    count += check_array_constructor_failures(run, exe, args.cc, args.node, args.validator, out)
    from wasm_fixed_argument_checks import check_images as check_fixed_argument_images, check_aliases as check_fixed_argument_aliases, check_guards as check_fixed_argument_guards, check_dynamic as check_fixed_argument_dynamic
    count += check_fixed_argument_images(run, args.node, args.validator, out)
    count += check_fixed_argument_aliases(run, args.node, args.validator, out)
    count += check_fixed_argument_guards(run, exe, args.cc, out)
    count += check_fixed_argument_dynamic(run, args.node, args.validator, out)
    from wasm_fixed_negation_checks import check_images as check_fixed_negation_images, check_loop as check_fixed_negation_loop
    count += check_fixed_negation_images(run, args.node, args.validator, out)
    count += check_fixed_negation_loop(run, args.node, args.validator, out)
    from wasm_compound_math_checks import check_images as check_compound_images, check_snapshot as check_compound_snapshot, check_loops as check_compound_loops, check_global as check_compound_global, check_failures as check_compound_failures
    count += check_compound_images(run, args.node, args.validator, out)
    count += check_compound_snapshot(run, args.node, args.validator, out)
    count += check_compound_loops(run, args.node, args.validator, out)
    count += check_compound_global(run, args.node, args.validator, out)
    count += check_compound_failures(run, exe, args.cc, args.node, args.validator, out)
    from wasm_fixed_binary_checks import check_images as check_fixed_binary_images, check_snapshot as check_fixed_binary_snapshot, check_loop as check_fixed_binary_loop, check_failures as check_fixed_binary_failures
    count += check_fixed_binary_images(run, args.node, args.validator, out)
    count += check_fixed_binary_snapshot(run, args.node, args.validator, out)
    count += check_fixed_binary_loop(run, args.node, args.validator, out)
    count += check_fixed_binary_failures(run, exe, args.cc, args.node, args.validator, out)
    from wasm_negation_adaptation_checks import check_images as check_negation_adaptation_images, check_prefixes as check_negation_adaptation_prefixes, check_loop as check_negation_adaptation_loop
    count += check_negation_adaptation_images(run, args.node, args.validator, out)
    count += check_negation_adaptation_prefixes(run, args.node, args.validator, out)
    count += check_negation_adaptation_loop(run, args.node, args.validator, out)
    from wasm_temporary_equality_checks import check_images as check_temporary_equality_images, check_guards as check_temporary_equality_guards
    count += check_temporary_equality_images(run, args.node, args.validator, out)
    count += check_temporary_equality_guards(run, exe, args.cc, out)
    from wasm_temporary_read_checks import check_images as check_temporary_read_images, check_guards as check_temporary_read_guards
    count += check_temporary_read_images(run, args.node, args.validator, out)
    count += check_temporary_read_guards(run, exe, args.cc, out)
    from wasm_array_result_checks import check_images as check_array_result_images, check_guards as check_array_result_guards, check_failures as check_array_result_failures, check_data as check_array_result_data
    count += check_array_result_images(run, args.node, args.validator, out)
    count += check_array_result_guards(run, exe, args.cc, out)
    count += check_array_result_failures(run, exe, args.cc, args.node, args.validator, out)
    count += check_array_result_data(run, args.node, args.validator, out)
    from wasm_array_argument_checks import check_images as check_array_argument_images, check_aliases as check_array_argument_aliases, check_guards as check_array_argument_guards
    count += check_array_argument_images(run, args.node, args.validator, out)
    count += check_array_argument_aliases(run, args.node, args.validator, out)
    count += check_array_argument_guards(run, exe, args.cc, out)
    from wasm_fixed_result_checks import check_images as check_fixed_result_images, check_guards as check_fixed_result_guards, check_failure as check_fixed_result_failure, check_target_failure as check_fixed_result_target_failure, check_nonlocal_guard as check_fixed_result_nonlocal_guard
    count += check_fixed_result_images(run, args.node, args.validator, out)
    count += check_fixed_result_guards(run, exe, args.cc, out)
    count += check_fixed_result_failure(run, exe, args.cc, args.node, args.validator, out)
    count += check_fixed_result_target_failure(run, exe, args.cc, args.node, args.validator, out)
    count += check_fixed_result_nonlocal_guard(run, exe, args.cc, out)
    count += check_data_iteration_footprint(run, exe, args.cc, args.node, args.validator, args.wasmtime_python, out,
                                          correctness_only=args.correctness_only)
    growth_source = out / 'frame-growth.goose'
    lines = ['recursive fn grow(n: i64) -> i64 {']
    for i in range(96):
        lines += [f'var a{i}: i64 = 1;', f'let r{i} = &a{i};']
    lines += ['if n > 0 { a0 += grow(n - 1); }',
              'return ' + ' + '.join(f'r{i}' for i in range(96)) + ';',
              '}', 'fn main() { print(grow(100)); }']
    growth_source.write_text('\n'.join(lines) + '\n')
    for opt in (0, 2):
        wasm = out / f'frame-growth-O{opt}.wasm'
        run([exe, f'-O{opt}', '--target', 'wasm', '-o', wasm, growth_source])
        run([args.validator, 'validate', wasm])
        result = run([args.node, ROOT / 'test' / 'wasm_runtime.mjs', wasm, 'growth'])
        assert result.stdout == b'9696\n'
        count += 1
        if args.wasmtime_python:
            assert run([args.wasmtime_python, ROOT / 'test' / 'wasmtime_host.py', wasm]).stdout == result.stdout
            count += 1
        # Set Memory 0's maximum to its initial page count. This changes only
        # the test module's resource limit and makes memory.grow fail for real.
        def leb(data, pos):
            value, shift = 0, 0
            while True:
                byte = data[pos]
                pos += 1
                value |= (byte & 127) << shift
                if not byte & 128:
                    return value, pos
                shift += 7
        original = wasm.read_bytes()
        cursor = 8
        sections = bytearray(original[:8])
        while cursor < len(original):
            start = cursor
            ident = original[cursor]
            length, body = leb(original, cursor + 1)
            cursor = body + length
            if ident == 5:
                assert original[body:body + 3] == b'\x01\x01\x01', 'expected one Memory32 with minimum one page'
                sections += b'\x05\x04\x01\x01\x01\x01'
            else:
                sections += original[start:cursor]
        limited = out / f'frame-growth-limited-O{opt}.wasm'
        limited.write_bytes(sections)
        run([args.validator, 'validate', limited])
        run([args.node, ROOT / 'test' / 'wasm_runtime.mjs', limited, 'growth-failure'])
        count += 1
    # Constructor scratch must be bounded independently of literal length.
    # The old emitter produced 56,015 locals and failed validation at 14,000
    # elements. Also exercise one whole-reservation memory.grow for a payload.
    for name, typ, length, mode in [('local-limit', 'u8[u16]', 14000, ''),
                                    ('variable-growth', 'i64[]', 9000, 'variable-growth')]:
        source = out / (name + '.goose')
        values = ', '.join('1' if name == 'local-limit' else str(i) for i in range(length))
        body = f'print(a.len, ",", a[{length - 1}]);'
        source.write_text(f'fn main() {{ var a: {typ} = [{values}]; {body} }}\n')
        expected = b'14000,1\n' if name == 'local-limit' else b'9000,8999\n'
        for opt in (0, 2):
            prefix = out / f'{name}-O{opt}'
            c, native, wasm = prefix.with_suffix('.c'), prefix.with_suffix('.native'), prefix.with_suffix('.wasm')
            run([exe, f'-O{opt}', '--standalone', '-o', c, source])
            run([args.cc, '-O0', c, '-pthread', '-lm', '-ldl', '-o', native])
            assert run([native]).stdout == expected
            run([exe, f'-O{opt}', '--target', 'wasm', '-o', wasm, source])
            assert max(function_local_counts(wasm.read_bytes())) <= 128, 'constructor scratch grew with literal length'
            run([args.validator, 'validate', wasm])
            actual = run([args.node, ROOT / 'test' / 'wasm_multimemory.mjs', wasm, '0', mode])
            assert actual.stdout == expected
            count += 1
            if args.wasmtime_python:
                assert run([args.wasmtime_python, ROOT / 'test' / 'wasmtime_host.py', wasm]).stdout == expected
                count += 1
    # A native-valid runtime capacity can exceed the entire Memory32 byte
    # range. Reject it before reservation; this test never requests gigabytes.
    overflow = out / 'runtime-capacity-overflow.goose'
    overflow.write_text('fn main() { var n: i64 = 4294967295; var a: u8[..] = [..n]; print(a.cap); }\n')
    run([exe, 'check', overflow])
    for opt in (0, 2):
        wasm = out / f'runtime-capacity-overflow-O{opt}.wasm'
        run([exe, f'-O{opt}', '--target', 'wasm', '-o', wasm, overflow])
        run([args.validator, 'validate', wasm])
        run([args.node, ROOT / 'test' / 'wasm_multimemory.mjs', wasm, '0', 'allocation-failure'])
        count += 1
        if args.wasmtime_python:
            failure = run([args.wasmtime_python, ROOT / 'test' / 'wasmtime_host.py', wasm], ok=False)
            assert failure.returncode and b'out of memory growing data storage' in failure.stderr and not failure.stdout
            count += 1
    # Deterministic values exercise arithmetic at each declared storage width,
    # independent of constant folding and of the receiving slot's width.
    randomizer = random.Random(20261106)
    lines = ['fn main() {']
    for width in (8, 16, 32, 64):
        for unsigned in (False, True):
            typ = ('u' if unsigned else 'i') + str(width)
            low, high = (0, 2**width - 1) if unsigned else (-2**(width-1), 2**(width-1)-1)
            for sample in range(12):
                a, b = randomizer.randint(low, high), randomizer.randint(low, high) or 1
                lines += ['{', f'var a: {typ} = {a};', f'var b: {typ} = {b};', f'var shift = {sample * 7};']
                for operator in ('+', '-', '*', '/', '%', '&', '|', '^'):
                    lines.append(f'print(a {operator} b);')
                lines += ['print(a << shift, ",", a >> shift);',
                          'print(a < b, a <= b, a > b, a >= b, a == b, a != b);', '}']
    for width, encoding in ((32, 'f'), (64, 'd')):
        for sample in range(40):
            while True:
                bits = randomizer.getrandbits(width)
                value = struct.unpack('<' + encoding, bits.to_bytes(width // 8, 'little'))[0]
                if math.isfinite(value):
                    break
            literal = repr(value)
            lines += ['{', f'var f: f{width} = {literal};', 'print(f);', '}']
    lines += ['}']
    numeric = out / 'numeric.goose'
    numeric.write_text('\n'.join(lines) + '\n')
    for opt in (0, 2):
        c, native, wasm = out / f'numeric-O{opt}.c', out / f'numeric-O{opt}.native', out / f'numeric-O{opt}.wasm'
        run([exe, f'-O{opt}', '--standalone', '-o', c, numeric])
        run([args.cc, f'-O{opt}', c, '-pthread', '-lm', '-ldl', '-o', native])
        reference = run([native])
        run([exe, f'-O{opt}', '--target', 'wasm', '-o', wasm, numeric])
        run([args.validator, 'validate', wasm])
        assert run([args.node, ROOT / 'scripts' / 'run_wasm.mjs', wasm]).stdout == reference.stdout, ('numeric', opt)
        count += 1
        if args.wasmtime_python:
            assert run([args.wasmtime_python, ROOT / 'test' / 'wasmtime_host.py', wasm]).stdout == reference.stdout, ('numeric Wasmtime', opt)
            count += 1
    # A chain of array-reference element types must not validate each
    # element twice recursively. The old lowering exceeds this compile limit.
    deep = out / 'nested-inline-types.goose'
    typ = 'i64[1]' + '&[1]' * 39
    deep.write_text('fn inspect(a: ' + typ + '?) { print(a == null); }\n'
                    'var unused: ' + typ + '? = null;\n'
                    'fn main() { inspect(unused); }\n')
    for opt in (0, 2):
        prefix = out / f'nested-inline-types-O{opt}'
        c, native, wasm = prefix.with_suffix('.c'), prefix.with_suffix('.native'), prefix.with_suffix('.wasm')
        run([exe, f'-O{opt}', '--standalone', '-o', c, deep])
        run([args.cc, '-O2', c, '-pthread', '-lm', '-ldl', '-o', native])
        assert run([native]).stdout == b'true\n'
        run([exe, f'-O{opt}', '--target', 'wasm', '-o', wasm, deep], timeout=5)
        run([args.validator, 'validate', wasm])
        assert run([args.node, ROOT / 'scripts' / 'run_wasm.mjs', wasm]).stdout == b'true\n'
        count += 1
        if args.wasmtime_python:
            assert run([args.wasmtime_python, ROOT / 'test' / 'wasmtime_host.py', wasm]).stdout == b'true\n'
            count += 1
    # Exercise the binary encoder itself with true multi-memory memargs and
    # signed LEB boundary values, independent of Goose storage lowering.
    binary_test, binary_module = out / 'wasm-binary-test', out / 'encoder.wasm'
    run([args.cxx, '-std=c++20', '-O0', ROOT / 'test' / 'wasm_binary.cpp', '-o', binary_test])
    overflow = run([binary_test, 'overflow'], ok=False)
    if overflow.returncode == 77:
        print('skip valid >4GiB span check: this host cannot provide its bounded virtual mapping')
    else:
        assert not overflow.returncode, overflow.stderr
        count += 1
    run([binary_test, binary_module])
    run([args.validator, 'validate', binary_module])
    js = """const fs=require('node:fs'), a=require('node:assert/strict');
const x=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[1]))).exports;
const values=[0n,63n,64n,127n,128n,-64n,-65n,-128n,-129n,-9223372036854775808n,9223372036854775807n];
values.forEach((v,i)=>a.equal(x['constant'+i](),v)); a.equal(x.unaligned(),values[9]);
const bytes=new Uint8Array(x.memory.buffer);
a.equal(bytes[8],65); a.equal(bytes[131081],90); a.equal(bytes[131089],81);
a.ok(bytes.subarray(9,131081).every(v=>v===0));
a.ok(bytes.subarray(131082,131089).every(v=>v===0)); a.equal(x.test_top.value,131104);
a.equal(new DataView(x.other.buffer).getBigInt64(1,true),values[9]);
a.equal(new DataView(x.memory.buffer).getBigInt64(1,true),65n<<56n);"""
    run([args.node, '-e', js, binary_module])
    count += 1
    bounded = out / 'bounded-conversion.goose'
    bounded.write_text("""fn main() {
    var value = -3.75;
    for i in 8 {
        assert((value as! i64) == i / 2 - 3);
        value += 0.5;
    }
    var single: f32 = -3.75;
    for i in 8 {
        assert((single as! i16) == i / 2 - 3);
        single += 0.5;
    }
    var unsigned_value = 300.5;
    assert((unsigned_value as! u8) == 44);
    assert((unsigned_value as! u64) == 300);
    var negative = -3.75;
    assert((negative as! u64) == 18446744073709551613);
    var lower = -9223372036854775808.0;
    assert((lower as! i64) == -9223372036854775808);
    var upper = 9223372036854774784.0;
    assert((upper as! i64) == 9223372036854774784);
}\n""")
    for opt in (0, 2):
        wasm = out / f'bounded-conversion-O{opt}.wasm'
        c, native = out / f'bounded-conversion-O{opt}.c', out / f'bounded-conversion-O{opt}.native'
        run([exe, f'-O{opt}', '--standalone', '-o', c, bounded])
        run([args.cc, f'-O{opt}', c, '-pthread', '-lm', '-ldl', '-o', native])
        assert run([native]).stdout == b''
        run([exe, f'-O{opt}', '--target', 'wasm', '-o', wasm, bounded])
        run([args.validator, 'validate', wasm])
        run([args.node, ROOT / 'test' / 'wasm_conversion.mjs', wasm])
        count += 1
        if args.wasmtime_python:
            assert run([args.wasmtime_python, ROOT / 'test' / 'wasmtime_host.py', wasm]).stdout == b''
            count += 1
    # Known runtime failures must occur for the same operation, not just any trap.
    failures = [
        ('varint-index', 'var a: u8[varint] = [7; 128]; print("bad=", a[failure_index]);', b'array index out of bounds'),
        ('assert', 'assert(false);', b'assert failed'),
        ('zero', 'var n = 0; print(7 / n);', b'division by zero'),
        ('byte-print-zero', 'var a: u8[] = [65]; var n = 0; print("bad=", a, 7 / n);', b'division by zero'),
        ('divoverflow', 'var n = -9223372036854775808; var m = -1; print(n / m);', b'overflow'),
        ('array-index', 'var a: i64[>..] = [1]; print("bad=", a[failure_index]);', b'out of bounds'),
        ('empty-pop', 'var a: i64[>..<] = []; print("bad=", a.pop());', b'empty'),
        ('inline-index', 'var a: i64[2] = [1, 2]; print("bad=", a[failure_index]);', b'out of bounds'),
        ('variable-index', 'var a: i64[] = [1]; print("bad=", a[failure_index]);', b'out of bounds'),
        ('runtime-index', 'var a: i64[..] = [..2]; a.push(1); print("bad=", a[failure_index]);', b'out of bounds'),
        ('runtime-capacity', 'var a: u8[..] = [..1]; a.push(1); print("bad=", a.push(2));', b'capacity'),
        ('runtime-zero', 'var a: u8[..] = [..0]; print("bad=", a.push(1));', b'capacity'),
        ('runtime-empty', 'var a: u8[..] = [..3]; print("bad=", a.pop());', b'empty'),
        ('runtime-negative', 'var n: i64 = -1; var a: i64[..] = [..n]; print("bad=", a.cap);', b'array capacity out of range'),
        ('runtime-large', 'var n: i64 = 4294967296; var a: i64[..] = [..n]; print("bad=", a.cap);', b'array capacity out of range'),
        ('limited-capacity', 'var a: u8[..1] = [1]; print("bad=", a.push(2));', b'capacity'),
        ('zero-capacity', 'var a: u8[..0] = []; print("bad=", a.push(1));', b'capacity'),
        ('limited-empty', 'var a: u8[..3] = []; print("bad=", a.pop());', b'empty'),
    ]
    for name, body, reason in failures:
        source = out / f'failure-{name}.goose'
        globals = ('var failure_index: i64 = 128;\n' if name == 'varint-index' else
                   'var failure_index: i64 = 1;\n' if name == 'runtime-index' else
                   'var failure_index: i64 = 2;\n' if name in ('array-index', 'inline-index', 'variable-index') else '')
        source.write_text(globals + 'fn main() { ' + body + ' }\n')
        for opt in (0, 2):
            wasm = out / f'failure-{name}-O{opt}.wasm'
            native = out / f'failure-{name}-O{opt}.native'
            c = native.with_suffix('.c')
            run([exe, f'-O{opt}', '--standalone', '-o', c, source])
            run([args.cc, c, '-pthread', '-lm', '-ldl', '-o', native])
            ref = run([native], ok=False)
            run([exe, f'-O{opt}', '--target', 'wasm', '-o', wasm, source])
            run([args.validator, 'validate', wasm])
            actual = run([args.node, ROOT / 'scripts' / 'run_wasm.mjs', wasm], ok=False)
            assert ref.returncode and actual.returncode, (name, opt, 'missing failure')
            native_reason = (b'index 128 out of bounds (length 128)' if name == 'varint-index' else
                             b'invalid capacity' if name in ('runtime-negative', 'runtime-large') else reason)
            assert native_reason in ref.stderr and reason in actual.stderr, (name, ref.stderr, actual.stderr)
            assert ref.stdout == actual.stdout == b'', (name, 'partial print leaked')
            if args.wasmtime_python:
                second = run([args.wasmtime_python, ROOT / 'test' / 'wasmtime_host.py', wasm], ok=False)
                assert second.returncode and reason in second.stderr and not second.stdout, (name, opt, second.stderr)
                count += 1
            count += 1
    # The checker can adapt an expression's type without changing its storage.
    # Copies must reject unequal layouts; fixed inline parameters use checked owners.
    for name, text in COPY_ADMISSION_CASES.items():
        source = out / f'copy-admission-{name}.goose'
        source.write_text(text + '\n')
        for opt in (0, 2):
            prefix = out / f'copy-admission-{name}-O{opt}'
            c, native, wasm = prefix.with_suffix('.c'), prefix.with_suffix('.native'), prefix.with_suffix('.wasm')
            run([exe, f'-O{opt}', '--standalone', '-o', c, source])
            run([args.cc, '-O0', c, '-pthread', '-lm', '-ldl', '-o', native])
            expected = b'1\n' if name.endswith('-argument') else b'3,1\n'
            assert run([native]).stdout == expected, (name, 'invalid native admission oracle')
            wasm.unlink(missing_ok=True)
            result = run([exe, f'-O{opt}', '--target', 'wasm', '-o', wasm, source], ok=False)
            if name == 'inline-fixed-argument':
                assert result.returncode == 0 and not result.stderr
                run([args.validator, 'validate', wasm])
                assert run([args.node, ROOT / 'scripts/run_wasm.mjs', wasm]).stdout == expected
                if args.wasmtime_python:
                    assert run([args.wasmtime_python, ROOT / 'test/wasmtime_host.py', wasm]).stdout == expected
                count += 1
                continue
            assert result.returncode and copy_admission_reason(name) in result.stderr, (name, opt, result.stderr)
            assert not wasm.exists(), (name, opt, 'rejected copy left a partial module')
            count += 1
    # Array-valued temporaries need destination protection. Reject each valid
    # source for that reason at both levels, including fully inlined calls.
    index = 'fn index() -> i64 { var b: i64[>..] = [99]; return 0; }\n'
    array_results = {
        'call': 'fn make() -> i64[>..] { var a: i64[>..] = [7]; return a; }\n'
                + index + 'fn main() { print(make()[index()]); }\n',
        'block': index + 'fn main() { print(({ var a: i64[>..] = [7]; copy(a) })[index()]); }\n',
        'branch': index + 'fn main() { var choose = true; print((if choose { '
                  'var a: i64[>..] = [7]; copy(a) } else { var b: i64[>..] = [8]; copy(b) })[index()]); }\n',
    }
    for name, text in array_results.items():
        source = out / f'array-result-{name}.goose'
        source.write_text(text)
        for opt in (0, 2):
            prefix = out / f'array-result-{name}-O{opt}'
            c, native, wasm = prefix.with_suffix('.c'), prefix.with_suffix('.native'), prefix.with_suffix('.wasm')
            run([exe, f'-O{opt}', '--standalone', '-o', c, source])
            run([args.cc, '-O2', c, '-pthread', '-lm', '-ldl', '-o', native])
            assert run([native]).stdout == b'7\n', 'invalid native temporary-result oracle'
            wasm.unlink(missing_ok=True)
            result = run([exe, f'-O{opt}', '--target', 'wasm', '-o', wasm, source], ok=False)
            assert result.returncode and b'wasm target:' in result.stderr and b'destination' in result.stderr
            assert not wasm.exists(), 'unsupported array result left a partial module'
            count += 1
    # Fixed-array equality captures the left value before RHS effects.
    # Fixed numeric unary arrays use the same checked destination path.
    pending_ops = [
        ('effectful-equality', 'fn change(a: i64[2]&, b: i64[2]&) -> i64[2]& { a[0] = 9; return b; }\n'
         'fn main() { var a: i64[2] = [1, 2]; var b: i64[2] = [1, 2]; print(a == change(a, b)); print(a[0]); }\n', b'true\n9\n'),
        ('unary-array', 'fn main() { var a: i64[2] = [1, 2]; var b: i64[2] = [-1, -2]; print(-a == b); }\n', b'true\n'),
    ]
    for name, text, expected in pending_ops:
        source = out / (name + '.goose'); source.write_text(text)
        for opt in (0, 2):
            prefix = out / f'{name}-O{opt}'
            c, native, wasm = prefix.with_suffix('.c'), prefix.with_suffix('.native'), prefix.with_suffix('.wasm')
            run([exe, f'-O{opt}', '--standalone', '-o', c, source])
            run([args.cc, '-O2', c, '-pthread', '-lm', '-ldl', '-o', native])
            assert run([native]).stdout == expected
            wasm.unlink(missing_ok=True)
            result = run([exe, f'-O{opt}', '--target', 'wasm', '-o', wasm, source], ok=False)
            if name in ('effectful-equality', 'unary-array'):
                assert result.returncode == 0 and not result.stderr
                run([args.validator, 'validate', wasm])
                assert run([args.node, ROOT / 'scripts/run_wasm.mjs', wasm]).stdout == expected
                if args.wasmtime_python:
                    assert run([args.wasmtime_python, ROOT / 'test/wasmtime_host.py', wasm]).stdout == expected
                restored = run([args.node, ROOT / 'test/wasm_multimemory.mjs', wasm, '0', 'no-data'])
                assert restored.stdout == expected and not restored.stderr
            else:
                assert result.returncode and b'destination' in result.stderr and not wasm.exists()
            count += 1
    # The explicit backend limit must reject a valid program before writing
    # any output. Keep every owner live to avoid testing dead-code removal.
    limit = out / 'data-memory-limit.goose'
    lines = ['fn main() {']
    for i in range(65):
        lines += [f'var a{i}: i64[>..] = [];', f'a{i}.push({i});']
    lines += ['print(' + ' + '.join(f'a{i}[0]' for i in range(65)) + ');', '}']
    limit.write_text('\n'.join(lines) + '\n')
    run([exe, 'check', limit])
    output = out / 'data-memory-limit.wasm'
    output.unlink(missing_ok=True)
    result = run([exe, '-O0', '--target', 'wasm', '-o', output, limit], ok=False)
    assert result.returncode and b'64 data-memory limit' in result.stderr
    assert not output.exists(), 'memory-limit failure left a partial module'
    count += 1
    # No stubs, no native extern reinterpretation, and no partial output on error.
    unsupported = [
        ('array', 'fn main() { var a = [1, 2]; print(a); }', b'layout'),
        ('export', 'export fn twice(x: i64) -> i64 { return x * 2; } fn main() {}', b'export'),
        ('extern', 'extern fn abs(x: i64) -> i64; fn main() { print(abs(-7)); }', b'extern'),
        ('nonlocal', 'fn a() -> i64 { return b(); } fn b() -> i64 { return 7 from a; } fn main() { print(a()); }', b'nonlocal'),
    ]
    for name, text, reason in unsupported:
        source, wasm = out / f'unsupported-{name}.goose', out / f'unsupported-{name}.wasm'
        source.write_text(text + '\n')
        wasm.unlink(missing_ok=True)
        result = run([exe, '-O0', '--target', 'wasm', '-o', wasm, source], ok=False)
        assert result.returncode and b'wasm target:' in result.stderr and reason in result.stderr, (name, result.stderr)
        assert not wasm.exists(), (name, 'partial module')
        if name == 'nonlocal':
            run([exe, '-O2', '--target', 'wasm', '-o', wasm, source])
            run([args.validator, 'validate', wasm])
            assert run([args.node, ROOT / 'scripts' / 'run_wasm.mjs', wasm]).stdout == b'7\n'
            text = run([args.validator, 'print', wasm]).stdout
            assert b'(tag ' not in text and b'throw ' not in text, 'inlined return uses exceptions'
            count += 1
        count += 1
    fixture = ROOT / 'test' / 'wasm' / 'wasm_scalars.goose'
    for flags in (['--target'], ['--target', 'other'], ['--target', 'wasm', '--jit'],
                  ['run', '--target', 'wasm'], ['--target', 'wasm', '--debug']):
        result = run([exe, *flags, fixture], ok=False)
        assert result.returncode, flags
        count += 1
    # Percent substitution must finish before checking source/output identity.
    preserved = out / 'preserved.goose'
    original = b'fn main() { print(1); }\n'
    preserved.write_bytes(original)
    result = run([exe, '--target', 'wasm', '--multi-test', '-o', out / '%.goose', preserved], ok=False)
    assert b'must not overwrite' in result.stderr and b'--multi-test: exit 1' in result.stderr, result.stderr
    assert preserved.read_bytes() == original, 'source overwritten after percent expansion'
    count += 1
    # The build verb and flag form must emit exactly the same module bytes.
    flag, verb = out / 'flag.wasm', out / 'verb.wasm'
    run([exe, '--target', 'wasm', '-o', flag, fixture])
    run([exe, 'build', '--target', 'wasm', '-o', verb, fixture])
    assert flag.read_bytes() == verb.read_bytes()
    print(f'wasm backend: {count + 1} checks passed')


if __name__ == '__main__':
    main()
