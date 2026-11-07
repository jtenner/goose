"""Derived test exports and hard allocation limit, with no guest-code edits."""
def derive(binary, limit=False):
    pos=8
    def read():
        nonlocal pos
        value=shift=0
        while True:
            byte=binary[pos];pos+=1;value|=(byte&127)<<shift
            if not byte&128:return value
            shift+=7
    def encode(value):
        out=[]
        while True:
            byte=value&127;value>>=7;out.append(byte|(128 if value else 0))
            if not value:return bytes(out)
    assert binary[:8]==b'\0asm\x01\0\0\0'
    sections=[];memories=0
    while pos<len(binary):
        ident=binary[pos];pos+=1;length=read();start=pos;end=pos+length;body=binary[start:end]
        if ident==5:
            memories=read();parts=[encode(memories)]
            for index in range(memories):
                flags=read();minimum=read();maximum=read();assert flags==1
                if limit and index==1:assert minimum==1;maximum=1
                parts.extend([encode(flags),encode(minimum),encode(maximum)])
            assert pos==end;body=b''.join(parts)
        if ident==7:
            assert memories>=2
            count=read();parts=[encode(count+memories),binary[pos:end]]
            for index in range(memories):
                name=('test_stack_top_'+str(index)).encode();parts.extend([encode(len(name)),name,b'\x03',encode(index)])
            body=b''.join(parts)
        sections.append(bytes([ident])+encode(len(body))+body);pos=end
    return binary[:8]+b''.join(sections)
