from pathlib import Path
import sys,subprocess
p=Path(__file__).parent/sys.argv[1];p.mkdir(exist_ok=True)
args=sys.argv[2:];(p/'command.txt').write_text(repr(args)+'\n')
with (p/'check.stdout').open('wb') as o,(p/'check.stderr').open('wb') as e:
 a=subprocess.run(args,stdout=o,stderr=e)
(p/'check.exit').write_text(str(a.returncode)+'\n');print(p.name,'exit',a.returncode)
