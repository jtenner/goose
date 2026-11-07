# Functional evidence record limits

No performance samples have been taken in this stage.

The first native-oracle unit used owner 4036675 and ended with exit 1 because three new fixtures were invalid Goose inputs. Its original per-case stdout, stderr, exit files, result/identity manifests and initial unit output remain in oracle01. Its successful release check was recorded before the second unit.

The second unit used owner 4055375. Its golden script wrote its new per-case records to oracle02, but its wrapper still used oracle01 as the aggregate output path. It replaced oracle01/lease.json and oracle01/golden.stdout, golden.stderr and golden.exit. Those original aggregate files are not reconstructed or claimed unchanged. The actual second aggregate files were copied to oracle02; record-correction.json records their provenance.

A premature handoff claimed the second fresh lock probe before checking the verifier result. That verifier had failed because oracle02/lease.json was missing; a later shell command had masked its failure status. The claim was immediately corrected. The actual deferred verification passed at the time in oracle02/release-verification.json, after E22 released. No active resource job was interrupted.

The final arrays fixture replaces an invalid zero-capacity array field with a positive-capacity field and zero-count fill. Native O0/O2 execution passed in build01. The earlier invalid inputs are preserved in their failed attempts.

All later units take an explicit, separate output directory. The wrapper refuses to overwrite a lease or unit log. Tool return codes are checked before any dependent release claim or thread handoff.
