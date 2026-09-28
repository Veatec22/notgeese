"""Small unsigned UE4.27 IoStore v3 overlays; never repack the game container.

Layout references: CUE4Parse UE4/IO/Objects (FIoContainerHeader,
FFilePackageStoreEntry, FIoStoreTocEntryMeta, FIoChunkId).
Only uncompressed v3 inputs are supported by this builder.
"""
import hashlib
import struct
from pathlib import Path

NONE = 0xffffffff

def u32(data, at): return struct.unpack_from('<I', data, at)[0]
def fs(text):
    data = text.encode() + b'\0'
    return struct.pack('<I', len(data)) + data

class Store:
    def __init__(self, base):
        self.base = Path(base)
        d = self.data = self.base.with_suffix('.utoc').read_bytes()
        assert d[:16] == b'-==--==--==--==-'
        assert d[16] == 3 and d[80] == 8
        h,n,bc,be,methods,mw,bs,ds,pc = struct.unpack_from('<9I', d,20)
        assert (h,be,methods,pc) == (144,12,0,1)
        self.block_size = bs
        self.ids = [d[h+i*12:h+(i+1)*12] for i in range(n)]
        a = h+n*12
        self.chunks = [(int.from_bytes(d[a+i*10:a+i*10+5],'big'),int.from_bytes(d[a+i*10+5:a+i*10+10],'big')) for i in range(n)]
        a += n*10
        self.blocks = [d[a+i*12:a+(i+1)*12] for i in range(bc)]
        a += bc*12
        end = a+ds
        def string():
            nonlocal a
            size=u32(d,a); a+=4
            assert 0<size<10000
            value=d[a:a+size-1].decode();a+=size
            return value
        assert string() == '../../../'
        def array(fmt):
            nonlocal a
            count=u32(d,a);a+=4;size=struct.calcsize(fmt)
            result=[struct.unpack_from(fmt,d,a+i*size) for i in range(count)];a+=count*size
            return result
        dirs=array('<4I'); files=array('<3I')
        count=u32(d,a);a+=4;strings=[string() for _ in range(count)]
        assert a==end and len(d)-end==n*33
        self.meta=[d[end+i*33:end+(i+1)*33] for i in range(n)]
        self.paths={}
        def walk(i,prefix):
            _,child,_,file=dirs[i]
            while child!=NONE:
                walk(child,prefix+strings[dirs[child][0]]+'/');child=dirs[child][2]
            while file!=NONE:
                name,next_file,index=files[file]
                self.paths[prefix+strings[name]]=index;file=next_file
        walk(0,'')

    def read(self,index):
        offset,size=self.chunks[index];out=bytearray();bs=self.block_size
        with self.base.with_suffix('.ucas').open('rb') as f:
            for i in range(offset//bs,(offset+size-1)//bs+1):
                b=self.blocks[i]; physical=int.from_bytes(b[:5],'little');cs=int.from_bytes(b[5:8],'little');us=int.from_bytes(b[8:11],'little')
                assert b[11]==0 and cs==us
                f.seek(physical);raw=f.read(cs);assert len(raw)==cs
                out+=raw[max(0,offset-i*bs):min(us,offset+size-i*bs)]
        assert len(out)==size
        assert self.meta[index][:32]==hashlib.sha1(out).digest()+bytes(12)
        return bytes(out)

    def package_entry(self, package_id):
        indices=[i for i,x in enumerate(self.ids) if x[11]==10]
        assert len(indices)==1
        b=self.read(indices[0])
        # UE4 empty redirect name batch: names buffer, hashes buffer.
        names=u32(b,12);assert names==0
        hashes=u32(b,16);a=20+hashes
        count=u32(b,a);a+=4
        ids=[b[a+i*8:a+(i+1)*8] for i in range(count)];a+=count*8
        size=u32(b,a);a+=4
        i=ids.index(package_id);at=a+i*32
        entry=bytearray(b[at:at+32]);num,relative=struct.unpack_from('<II',entry,24)
        imports=b[at+24+relative:at+24+relative+num*8] if num else b''
        assert len(imports)==num*8 and at+32<=a+size
        return entry,imports,b[12:20+hashes]

def directory(paths):
    strings=[];dirs=[[NONE,NONE,NONE,NONE]];files=[];known={'':0}
    def name(value):
        if value not in strings:strings.append(value)
        return strings.index(value)
    for path,index in paths.items():
        parts=path.split('/');parent=0;prefix=''
        for part in parts[:-1]:
            prefix+=part+'/'
            if prefix not in known:
                child=len(dirs);known[prefix]=child
                dirs.append([name(part),NONE,dirs[parent][1],NONE]);dirs[parent][1]=child
            parent=known[prefix]
        files.append([name(parts[-1]),dirs[parent][3],index]);dirs[parent][3]=len(files)-1
    return (fs('../../../')+struct.pack('<I',len(dirs))+b''.join(struct.pack('<4I',*x) for x in dirs)
            +struct.pack('<I',len(files))+b''.join(struct.pack('<3I',*x) for x in files)
            +struct.pack('<I',len(strings))+b''.join(fs(x) for x in strings))

def write_overlay(source, replacements, base):
    """Only explicitly supplied localization packages and their minimal store entries."""
    assert replacements
    cid=hashlib.sha1(base.name.encode()).digest()[:8]
    chunks=[];entries=[];imports=[];ids=[];paths={};names=None
    for path,body in replacements.items():
        index=source.paths[path];chunk_id=source.ids[index];assert chunk_id[11]==2
        original=source.read(index)
        entry,dependencies,names=source.package_entry(chunk_id[:8])
        old=struct.unpack_from('<Q',entry)[0]
        struct.pack_into('<Q',entry,0,old+len(body)-len(original))
        entries.append(entry);imports.append(dependencies);ids.append(chunk_id[:8])
        paths[path]=len(chunks);chunks.append((chunk_id,body))
    table=bytearray();deps=bytearray()
    for i,(entry,dependencies) in enumerate(zip(entries,imports)):
        struct.pack_into('<I',entry,28,len(entries)*32+len(deps)-(i*32+24) if dependencies else 0)
        table+=entry;deps+=dependencies
    table+=deps
    header=cid+struct.pack('<I',len(ids))+names+struct.pack('<I',len(ids))+b''.join(ids)+struct.pack('<I',len(table))+table+struct.pack('<II',0,0)
    chunks.append((cid+b'\0\0\0\x0a',header))
    bs=65536;data=bytearray();offsets=bytearray();blocks=bytearray();meta=bytearray()
    for chunk_id,body in chunks:
        logical=(len(blocks)//12)*bs
        offsets+=logical.to_bytes(5,'big')+len(body).to_bytes(5,'big')
        for at in range(0,len(body),bs):
            part=body[at:at+bs];blocks+=len(data).to_bytes(5,'little')+len(part).to_bytes(3,'little')*2+b'\0';data+=part
        meta+=hashlib.sha1(body).digest()+bytes(13)
    listing=directory(paths)
    toc=bytearray(144);toc[:16]=b'-==--==--==--==-';toc[16]=3
    struct.pack_into('<9I',toc,20,144,len(chunks),len(blocks)//12,12,0,32,bs,len(listing),1)
    toc[56:64]=cid;toc[80]=8;struct.pack_into('<Q',toc,88,0xffffffffffffffff)
    toc+=b''.join(x[0] for x in chunks)+offsets+blocks+listing+meta
    base.parent.mkdir(parents=True,exist_ok=True)
    base.with_suffix('.ucas').write_bytes(data);base.with_suffix('.utoc').write_bytes(toc)
    check=Store(base)
    assert set(check.paths)==set(replacements)
    for path,body in replacements.items():assert check.read(check.paths[path])==body
    for package_id in ids:check.package_entry(package_id)
    return {'packages':list(replacements),'ucas_bytes':len(data),'utoc_bytes':len(toc)}
