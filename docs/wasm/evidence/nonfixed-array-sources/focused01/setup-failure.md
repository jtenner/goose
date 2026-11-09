# Focused setup failure

The fixture-copy step completed. Before the backend harness was written, the
setup script searched for a following sibling if after the aggregate-prefix
owner block and raised ValueError: substring not found. The check script was
therefore not written; the attempted wrapper exited2 without compiler/guest
commands. The fix inserts the new sibling before the known aggregate block.
No production compiler change or rebuild is required.
