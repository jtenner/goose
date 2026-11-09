from pathlib import Path
import json,hashlib
p=Path(__file__).parent;d=p/'guard-sources';d.mkdir(exist_ok=True)
cases={'equality':'struct S{n:i64}fn main(){var a:S[varint]=[S{7}];assert(a==a);print("guard");}\n','zero':'enum E{A,B{n:u8}}fn main(){var a:E.A[varint]=[E.A;2];assert(a.len==2);print("guard");}\n'}
rows=[]
for name,s in cases.items():(d/(name+'.goose')).write_text(s);rows.append({'case':name,'source_sha256':hashlib.sha256(s.encode()).hexdigest(),'expected':'guard\n'})
(p/'guard-families.json').write_text(json.dumps(rows,indent=2)+'\n')
s=(p/'parent_checks01.py').read_text().replace("p/'parent01'","p/'parent05'").replace("p/'prepared-families.json'","p/'guard-families.json'").replace("p/'prepared'/","p/'guard-sources'/").replace("'producer_phase':'parent01'","'producer_phase':'parent05'");(p/'parent_checks05.py').write_text(s)
