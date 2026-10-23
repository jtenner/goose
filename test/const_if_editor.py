"""LSP refactoring regressions shared by the const-if layer acceptance runs."""
import subprocess
from lsp_protocol import Client


def check_editor(exe, root, core_only=False, fields_only=False):
    cases = [('condition', 'let CONFIG = true;\nfn main(){const if CONFIG {print(1);}}\n', 'CONFIG')]
    if not core_only:
        cases += [('condition', 'let CONFIG = true;\nstruct S {const if CONFIG {a:u8=1,} else {b:u8=2,}}\nfn main(){print(S{});}\n', 'CONFIG')]
    if not core_only and not fields_only:
        cases += [('condition', 'let CONFIG = true;\nstruct S {a:u8=1}\nfn main(){let s=S{const if CONFIG {a:2,},};print(s);}\n', 'CONFIG'),
                  ('field', 'struct S {chosen:u32=2}\nfn main(){let s=S{const if true {chosen:7,},};print(s.chosen);}\n', 'chosen')]
    checks = 0
    for i, (kind, text, name) in enumerate(cases):
        source = root / f'editor_{i}.goose'
        source.write_text(text)
        uri = source.as_uri()
        client = Client(str(exe), root)
        def position(offset):
            prefix = text[:offset]
            return {'line': prefix.count('\n'), 'character': len(prefix.rsplit('\n', 1)[-1])}
        try:
            client.request('initialize', {'processId': None, 'rootUri': root.as_uri(), 'capabilities': {},
                                         'initializationOptions': {'entryFiles': [str(source)]}})
            client.send('initialized', {}, request=False)
            client.send('textDocument/didOpen', {'textDocument': {'uri': uri, 'languageId': 'goose',
                                                                'version': 1, 'text': text}}, request=False)
            assert client.diagnostics_for(uri) == []
            use = text.rfind(name) if kind == 'condition' else text.index('chosen:7')
            doc = {'textDocument': {'uri': uri}, 'position': position(use + 1)}
            assert client.request('textDocument/hover', doc), (kind, 'hover')
            assert client.request('textDocument/definition', doc), (kind, 'definition')
            refs = client.request('textDocument/references', {**doc, 'context': {'includeDeclaration': True}})
            assert len(refs) == (2 if kind == 'condition' else 3), (text, refs)
            declaration = {'textDocument': {'uri': uri}, 'position': position(text.index(name) + 1)}
            edit = client.request('textDocument/rename', {**declaration, 'newName': 'renamed'})
            edits = edit['changes'][uri]
            assert len(edits) == (2 if kind == 'condition' else 3), (text, edits)
            lines = text.splitlines(keepends=True)
            def offset(p): return sum(map(len, lines[:p['line']])) + p['character']
            rewritten = text
            for e in sorted(edits, key=lambda e: offset(e['range']['start']), reverse=True):
                rewritten = rewritten[:offset(e['range']['start'])] + e['newText'] + rewritten[offset(e['range']['end']):]
            renamed = root / f'renamed_{i}.goose'
            renamed.write_text(rewritten)
            result = subprocess.run([str(exe), 'check', str(renamed)], capture_output=True, text=True)
            assert result.returncode == 0, (rewritten, result.stderr)
            client.request('shutdown', {})
            client.send('exit', {}, request=False)
            assert client.p.wait(timeout=10) == 0
            checks += 5
        finally:
            if client.p.poll() is None:
                client.p.kill()
                client.p.wait()
    return checks
