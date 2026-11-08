#!/usr/bin/env python3
"""Packed word declaration/field hovers in fresh configured editor sessions."""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from lsp_protocol import Client, uri_of

def check():
    exe=os.environ.get('GOOSE_TEST_EXE') or shutil.which('goose++');checks=0
    with tempfile.TemporaryDirectory(prefix='packed-editor-') as td:
        p=Path(td);source=p/'main.goose'
        text='''packed word Header:u64 {
 const if build::DEBUG { debug:bool } else { _:u1 },
 age:u7
}
fn main(){var w=Header{..}; print(w.age);}
'''
        source.write_text(text)
        for debug in ('true','false'):
            client=Client(exe,p,args=('-D','DEBUG='+debug))
            try:
                client.request('initialize',{'processId':None,'rootUri':uri_of(p),'capabilities':{},'initializationOptions':{'entryFiles':[str(source)]}})
                client.send('initialized',{},request=False)
                doc={'textDocument':{'uri':uri_of(source)}}
                client.send('textDocument/didOpen',{'textDocument':{'uri':uri_of(source),'languageId':'goose','version':1,'text':text}},request=False)
                diagnostics=client.diagnostics_for(uri_of(source))
                assert not diagnostics,diagnostics;checks+=1
                for line,col,want in ((0,13,'packed word Header : u64'),(2,2,'age: u7'),(4,36,'age: u7')):
                    got=client.request('textDocument/hover',{**doc,'position':{'line':line,'character':col}})
                    assert want in json.dumps(got),(line,col,got);checks+=1
                got=client.request('textDocument/documentSymbol',doc)
                assert 'Header' in json.dumps(got),got;checks+=1
            finally:
                client.request('shutdown',None);client.send('exit',request=False)
                assert client.p.wait(timeout=30)==0
    print(f'packed word editor: {checks} checks passed')
if __name__=='__main__':check()
