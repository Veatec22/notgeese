"""Read the inspected UE4.27 pak index and unencrypted raw/Oodle entries."""
import struct, hashlib, ctypes
from pathlib import Path
class Reader:
 def __init__(self,data): self.data=data; self.at=0
 def get(self,fmt):
  v=struct.unpack_from('<'+fmt,self.data,self.at); self.at+=struct.calcsize('<'+fmt); return v[0] if len(v)==1 else v
 def string(self):
  n=self.get('i'); b=self.data[self.at:self.at+abs(n)*(2 if n<0 else 1)]; self.at+=len(b); return b.decode('utf-16-le' if n<0 else 'utf-8').rstrip('\0')
class GamePak:
 def __init__(self,path,oodle=None):
  self.path=Path(path); self.oodle_path=oodle
  with self.path.open('rb') as f:
   f.seek(-221,2); foot=f.read(); assert foot[:17]==bytes(17)
   magic,version,off,size=struct.unpack_from('<IIqq',foot,17); assert magic==0x5a6f12e1 and version==11
   f.seek(off); data=f.read(size); assert hashlib.sha1(data).digest()==foot[41:61]
   r=Reader(data); self.mount=r.string(); self.count=r.get('I'); r.get('Q')
   if r.get('I'): r.at+=36
   assert r.get('I'); do,ds=r.get('qq'); dh=r.data[r.at:r.at+20]; r.at+=20
   n=r.get('I'); self.encoded=r.data[r.at:r.at+n]; r.at+=n; assert r.get('I')==0
   f.seek(do); directory=f.read(ds); assert hashlib.sha1(directory).digest()==dh
  r=Reader(directory); self.files={}
  for _ in range(r.get('I')):
   directory=r.string()
   for _ in range(r.get('I')):
    name=r.string(); self.files[directory+name]=r.get('i')
 def extract(self,path):
  r=Reader(self.encoded); r.at=self.files[path]; flags=r.get('I')
  blocksize=r.get('I') if flags&63==63 else (flags&63)<<11
  method=(flags>>23)&63; off=r.get('I' if flags&0x80000000 else 'Q'); usize=r.get('I' if flags&0x40000000 else 'Q')
  size=r.get('I' if flags&0x20000000 else 'Q') if method else usize
  assert not flags&(1<<22)
  with self.path.open('rb') as f:
   f.seek(off); header=f.read(53)
   if not method: return f.read(size)
   f.seek(off+28); digest=f.read(20); count=struct.unpack('<I',f.read(4))[0]
   blocks=[struct.unpack('<qq',f.read(16)) for _ in range(count)]
   encrypted,blocksize=struct.unpack('<BI',f.read(5)); assert not encrypted
   if not hasattr(self,'oodle'):
    if not self.oodle_path: raise ValueError('Supply the local Oodle library path for compressed entries.')
    dll=ctypes.CDLL(str(self.oodle_path))
    self.oodle=dll.OodleLZ_Decompress; self.oodle.restype=ctypes.c_longlong
    self.oodle.argtypes=[ctypes.c_void_p,ctypes.c_longlong,ctypes.c_void_p,ctypes.c_longlong,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_void_p,ctypes.c_longlong,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_longlong,ctypes.c_int]
   out=bytearray()
   for start,end in blocks:
    f.seek(off+start); src=f.read(end-start); n=min(blocksize,usize-len(out)); dst=ctypes.create_string_buffer(n)
    got=self.oodle(src,len(src),dst,n,1,0,0,None,0,None,None,None,0,3); assert got==n,(got,n,method)
    out+=dst.raw
   assert len(out)==usize
   return bytes(out)
