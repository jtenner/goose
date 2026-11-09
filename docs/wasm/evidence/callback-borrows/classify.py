from pathlib import Path
import subprocess,json
r=Path(__file__).parent;out=r/'classification01';exe=r/'build02/goose-tested';f=out/'optional.goose'
for label,args in [('native-emit',[exe,'-O0','--standalone','-o',out/'optional.c',f]),('native-build',['cc',out/'optional.c','-pthread','-lm','-ldl','-o',out/'optional.native']),('native-run',[out/'optional.native']),('wasm-emit',[exe,'-O0','--target','wasm','-o',out/'optional.wasm',f]),('node',['node','test/wasm_reference_abi.mjs',out/'optional.wasm',out/'optional-instance'])]:
 args=list(map(str,args));a=subprocess.run(args,capture_output=True,timeout=120);p=out/label;p.with_suffix('.json').write_text(json.dumps(args)+'\n');p.with_suffix('.stdout').write_bytes(a.stdout);p.with_suffix('.stderr').write_bytes(a.stderr);p.with_suffix('.exit').write_text(str(a.returncode)+'\n');print(label,a.returncode,a.stdout.decode(),a.stderr.decode()[-1000:])
 if a.returncode and label!='node':break
