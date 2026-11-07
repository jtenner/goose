from pathlib import Path
import json,hashlib
p=Path(__file__).parent
for n,h in json.loads((p/'input-hashes.json').read_text()).items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h,n
print('Preserved compiler and named-copy check inputs match.')
