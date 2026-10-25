# Benchmark artifacts, version 1

## Statistics and memory

For accepted measured elapsed seconds x[1..N], report count, median, unscaled
median absolute deviation `median(abs(x - median(x)))`, MAD percent
`100 * MAD / median`, minimum and maximum. For even N, median averages the two
middle values, including for MAD. Derive seconds from integer monotonic elapsed
nanoseconds. A nonpositive elapsed interval is an invalid measurement and fails
with a clock-resolution diagnostic, not a fake zero or infinite throughput.
Keep every attempt, including excluded warmups and thermal rejections. Do not
report a best-of-N headline, standard error, confidence interval, p95 or p99 from
seven observations. No assertion that five samples are statistically sufficient
for every workload; they are the minimum harness contract.

The benchmark returns its checksum, not a work-count structure. The command
reports seconds per call, not ns/op or units/s. Python knows suite work units
and may derive per-accepted-sample rates `units / seconds` and latencies
`seconds * 1e9 / units`, then aggregate each distribution as in the shared native
harness. Do not derive median throughput by inverting median time for even N.
Do not add mandatory workload metadata to every declaration just for reporting.

On Linux record kernel process peak RSS, normalized to bytes (getrusage/wait4
KiB multiplied by 1024), both at each completed call and at child exit. It
includes runtime and global fixtures. In reuse mode a call's reading is a
cumulative process high-water mark, not that call's incremental allocation or
peak. A row's `process_peak_rss_bytes` is the maximum final child high-water
mark over all its children, including warmups and thermal retries. Never
subtract setup RSS from a high-water mark. Return null with a reason if an
accurate native process-peak metric is unavailable. Parent/monitor/compiler
memory is excluded. This is resident memory, not reserved virtual memory and
not exact committed/payload bytes; no payload estimate is invented. For
independent per-call process peaks use process mode, still including setup.

## Human output and stable artifacts

Stdout is always a human table, one row per function/size: key, label, size,
isolation, accepted count, median ms, MAD %, min ms, max ms, maximum observed
Tctl C, thermal rejection count, process peak MiB, checksum and status. Print
units in headings, `n/a` for unavailable values, `UNGATED` for disabled thermal
control, and an explicit note that RSS is process lifetime. Long labels and
checksums may be visually truncated; files retain the complete data. A heading
identifies source, compiler/configuration, warmup count, gate and ceiling.
Failed/pending rows show statuses rather than invented numbers. Progress,
thermal waits and compiler/child diagnostics go to stderr. `--json PATH` and
`--csv PATH` write files, not alternate stdout protocols; `-` is not a file
option in v1.

Write UTF-8, locale-independent artifacts by temporary file plus atomic rename.
After each completed attempt checkpoint JSON when requested; finalize artifacts
on normal success, failure or handled interruption. A crash/SIGKILL can leave
only the last checkpoint. Do not promise recoverability before parsing the CLI
and output paths. CSV is written/finalized from the same in-memory records as
JSON; multi-file updates are not one atomic transaction. Match artifacts by
`run_id`. Incomplete runs must not be published as successful measurements.
The Python adapter should request JSON, the authoritative full artifact.

### JSON schema v1

The following is the exhaustive v1 field inventory, with types and semantics.
All fields listed are present; nullability is stated. No JSON NaN/Infinity.
Object field order is irrelevant; array order is meaningful. Consumers reject
unknown schema versions and tolerate unknown fields added within version 1.
Counts are nonnegative JSON integers. Elapsed nanoseconds are decimal strings
to preserve precision in common JSON clients; seconds are finite JSON numbers.
Checksum integer values are also strings, even when small. Paths are strings;
hashes are lowercase SHA-256 hex. Timestamps are UTC RFC 3339 strings.

Top-level object:

* `schema_version`: integer 1.
* `run_id`: unique UUID string, shared with CSV and log names.
* `status`: `running`, `ok`, `listed`, `failed`, or `interrupted`.
* `started_at`, `finished_at`: timestamps; finished is null while running.
* `source`: object with `path` (target's absolute path), `sha256` (target bytes),
  `files` (array of `{path, sha256}` for target, imported source and embedded
  input files used at compile time), `git_commit` (string or null), and
  `git_dirty` (bool or null, covers recorded source inputs, including untracked
  inputs). Runtime fixture files are the author's reproducibility obligation;
  there is no automatic transitive filesystem tracing.
* `host`: object with `os`, `kernel`, `architecture`, `cpu_model` (strings),
  `logical_cpus` (integer), `affinity` (array of effective CPU IDs or null),
  `clock` (monotonic clock identifier string), `clock_resolution_ns` (decimal
  string), and `memory_metric` (`linux_process_peak_rss` or `unavailable`).
* `toolchain`: object with `goose` and `cc`, each an object containing `path`,
  `sha256`, and `version` strings. Capture versions and hash actual binaries,
  not just invocation names; include selected compiler wrapper in flags when
  applicable. `cc` is null for listing/preflight before selection.
* `configurations`: array of configuration objects described below.
* `policy`: object with `samples` and `warmups` (requested accepted counts),
  `isolation` (`reuse` or `process`), `setup_timeout_seconds`,
  `sample_timeout_seconds`, `gate_timeout_seconds` (numbers), `max_retries`
  (integer per slot), and `thermal` (object below).
* `results`: array of row objects, in function source order then canonical size
  order. Configurations are included in each row's identity.
* `error`: null or `{code, message}` strings explaining the run-level failure.
  Codes: `usage`, `compile`, `selection`, `sensor`, `lock`, `setup`, `timeout`,
  `checksum`, `child_exit`, `protocol`, `thermal_retries`, `clock`, `io`,
  `interrupted`. A row may provide a more local copy of the same error.

Configuration object:

* `id`: SHA-256 of canonical JSON (sorted keys, compact UTF-8 encoding) of the
  effective configuration fields `size`, `definitions`, `goose_flags`,
  `native_flags`, plus toolchain executable hashes and recorded source hashes
  sorted by path. This is a configuration fingerprint, not a portable cache
  key across different absolute paths. During listing, use JSON null for an
  unselected C compiler hash; listing IDs must not be used as execution cache
  keys. Do not emit configurations whose source/option resolution failed.
* `size`: `small`, `medium`, or `large`.
* `definitions`: array sorted by name, each `{name, type, value}` with string
  type (`bool`, `i64`, `u64`, `string`); value is bool for bool, decimal string
  for integers, decoded string for strings. Includes `BENCH_SIZE`.
* `goose_flags`, `native_flags`: arrays of effective option strings in order,
  including optimization, checks, C macros, link options and backend choice.
* `executable_sha256`, `generated_c_sha256`: strings or null when not built.
  Hash immutable artifacts actually executed; never reuse a stale binary after
  a failed build. Check input/toolchain hashes have not changed during build.

Thermal policy object:

* `mode`: `required` or `disabled`.
* `reason`: null in normal required mode; diagnostic string on unavailable
  sensor or explicit disable (including whether discovery was skipped).
* `gate_c`, `ceiling_c`: finite numbers, retained even when disabled as requested
  settings; they are not enforced then.
* `poll_interval_ms`: requested number for active monitoring.
* `sensors`: array of `{id, chip, device_path, label, input_path}` strings;
  `label` is `Tctl`, `id` is the resolved input path. Empty when disabled or
  discovery failed. IDs are unique for the run, not stable hardware serials.

Result row:

* `key`, `label`: qualified function name and decoded label strings.
* `source_line`: 1-based declaration line integer in target file.
* `size`, `configuration_id`: variant name and configuration fingerprint.
* `status`: `pending`, `running`, `ok`, `listed`, `failed`, or `interrupted`.
* `isolation`: effective mode, repeated for standalone row consumers.
* `checksum`: null until the first completed call; otherwise a checksum object
  defined below. This is the expected checksum for all subsequent calls.
* `accepted_warmups`, `accepted_samples`, `thermal_rejections`: counts so far.
* `attempts`: array in execution order, defined below. Includes all warmups and
  rejections; no filtering needed to audit decisions.
* `summary`: null unless the row is complete and successful; otherwise
  `{median_seconds, seconds_mad, seconds_mad_percent, seconds_min, seconds_max}`,
  all numbers computed only over accepted measured calls.
* `temperature_max_observed_c`: number or null; maximum of this row's recorded
  bracket/in-call readings over all attempts (excluding gate wait readings).
* `process_peak_rss_bytes`: integer or null, lifetime maximum defined above.
* `memory_unavailable_reason`: string when RSS unavailable, otherwise null.
* `children`: array of `{id, exit_code, signal, process_peak_rss_bytes,
  stdout_path, stderr_path, logs_truncated}`. ID is a run-local integer; exit
  code and signal are integers or null before exit/when inapplicable; RSS is
  integer or null. Log paths are strings (empty logs still get files);
  `logs_truncated` is bool. Reuse normally has one child; process mode has one
  per attempt. Setup failures can leave a child without a timed attempt.
* `error`: null or `{code, message}` using the run error vocabulary.

Attempt object:

* `index`: 1-based attempt sequence within the row.
* `phase`: `warmup` or `measure`.
* `slot`: 1-based accepted-slot target within phase. Retries keep the same slot.
* `retry`: zero-based retry number for that slot.
* `child_id`: matching child record ID.
* `status`: `accepted`, `thermal_rejected`, `failed`, or `interrupted`.
* `elapsed_ns`: decimal string or null if no complete timed call; `seconds`:
  finite number derived from it or null.
* `checksum`: the observed typed checksum object, or null if no result. Retain
  the disagreeing value on failure rather than overwriting the row baseline.
* `gate_wait_seconds`: number for total wait before this attempt, including
  time spent discovering that the gate timed out.
* `temperature_before_c`, `temperature_after_c`, `temperature_max_observed_c`:
  numbers or null, maxima across the selected sensors at the corresponding
  reading(s). Null when disabled or no valid reading exists.
* `temperature_reads`: array of `{sensor_id, offset_ns, c}`. Offset is a signed
  decimal nanosecond string relative to the child's timer start using the same
  host clock; pre-read may be negative and post-read after elapsed_ns. `c` is
  a number. Store bracket/in-call reads, not every gate-wait poll. Empty when
  no call starts or temperature is disabled. Sensor failure is an error, not
  a fabricated read. Gate timeout explanation goes into `error`.
* `temperature_max_poll_gap_ms`: number or null; largest adjacent read gap per
  sensor including the bracketing endpoints. At least pre/post reads are
  required for every completed gated attempt.
* `process_peak_rss_bytes`: child's cumulative high-water reading at completion,
  integer or null; not a per-call peak in reuse mode.
* `error`: null or `{code, message}`. Thermal rejection uses null error and
  its status; exhaustion fails the row with `thermal_retries`.

Checksum object is `{components: [...]}`. Each ordered component is
`{type, value}`: `type` is one accepted scalar type. `value` is a decimal string
without leading zeros for integers (negative signed values have `-`), a JSON
boolean for bool, or a fixed-width lowercase IEEE hex string for floats
(`0x` plus 8 digits for f32 or 16 for f64, numerical bit order independent of
host endianness). An observed nonfinite float may be recorded as its hex bits
on the failed attempt; it can never yield an `ok` row. Example:

```json
{"components":[{"type":"i64","value":"16000000"},
               {"type":"u64","value":"18446744073709551615"},
               {"type":"f64","value":"0x3ff0000000000000"}]}
```

### CSV schema v1

`--csv results.csv` produces a summary file at that path and raw attempts at
`results.samples.csv` (insert `.samples` before the last extension; append it
if none). Use RFC 4180 quoting, header row, comma separator, UTF-8, decimal dot,
and empty cells for null. Booleans are lowercase `true`/`false`; JSON cells are
compact JSON with CSV escaping. Integer checksum strings stay inside JSON
cells; spreadsheet numeric inference must not corrupt them. Each summary row
represents one selected result, including failures and pending/listed rows.

Summary columns, in exact order:

```text
schema_version,run_id,key,label,source_path,source_sha256,source_line,size,configuration_id,isolation,status,thermal_mode,gate_c,ceiling_c,warmups_requested,samples_requested,accepted_warmups,accepted_samples,thermal_rejections,median_seconds,seconds_mad,seconds_mad_percent,seconds_min,seconds_max,temperature_max_observed_c,process_peak_rss_bytes,memory_unavailable_reason,checksum_json,error_code,error_message
```

All names map directly to the JSON definitions: source fields from `source`,
requests from `policy`, thermal fields from `policy.thermal`, statistics from
`row.summary`, other measurement fields from the row. `checksum_json` is the
entire checksum object; error columns flatten row error, falling back to the
run error for pending rows. Null summary produces empty statistic cells.

Raw attempt columns, in exact order:

```text
schema_version,run_id,key,size,configuration_id,index,phase,slot,retry,child_id,status,elapsed_ns,seconds,gate_wait_seconds,temperature_before_c,temperature_after_c,temperature_max_observed_c,temperature_max_poll_gap_ms,process_peak_rss_bytes,checksum_json,error_code,error_message
```

These map directly to the attempt; identifying fields come from its parent row
and run. There is no row for an attempt that never occurred. Full sensor traces,
child logs and toolchain provenance remain in JSON; CSV is an analysis/export
projection, not a replacement for the full reproducibility record. A CSV-only
consumer can compute timing distributions, identify exclusions, and join
summary to attempts by `(run_id, configuration_id, key)`.


## Configuration fingerprint encoding

The fingerprint input is one compact UTF-8 JSON object. Keys are sorted at every
level. The top-level keys are `cc_sha256`, `definitions`, `goose_flags`,
`goose_sha256`, `native_flags`, `size`, and `source_files`. `source_files` contains
`{path, sha256}` entries sorted by path. Standard JSON short escapes are used for
backspace, form feed, newline, carriage return, and tab. Other C0 controls use
lowercase `\u00xx` escapes; non-ASCII characters remain UTF-8.

`bench/native_results.py` reads and validates the full JSON artifact. It checks
the fingerprint, successful status, requested counts, typed checksums, durations,
and recomputed statistics. By default it rejects disabled thermal control.
The caller owns work units and cross-language checks. This adapter does not run
benchmarks or change the existing suite's timing scope or state format.

## Verification

`python3 test/bench_report.py` uses fixed sample records and a virtual thermal
clock. It checks both artifact formats and the Python adapter. It does not
execute `goose bench` or collect live timings. The declaration, native transport,
thermal integration, and baseline suites need separate approval when benchmark
execution is prohibited on a shared host.
