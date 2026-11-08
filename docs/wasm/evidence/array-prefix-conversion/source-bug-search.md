# Read-only source bug search

Native GPT-6.1-Sol high worker prefix_conversion_bug_search read the existing
array-place, reference, prefix, storage and native construction paths. It made
no edits and ran no build, guest, timing or lease command. No confirmed source
hole was found in the narrow proposed VariableArray source conversion.

The plan must preserve source-specific count/prefix capture, use a checked
zero-index ElementOffset before reserve, retain the packed memory identity,
check receiving prefix range and count-times-stride before allocation, and
copy only the active payload. Native codegen_construct.h checks receiving
prefix range and sets runtime capacity and length to active count.

Suggested cases were empty LEB, 127/128, target u8 counts 255/256, stored and
indexed references, reference-returning calls and source changes after copy.
These are test candidates, not execution evidence from the worker. Parent
execution records are separate. Four legacy admission expectations must change.
