"""Read-only probe of this game's uncompressed, unsigned IoStore v3.

Format reference: https://github.com/gitMenv/UEcastoc/blob/master/utoc.go
No serialization back to the game and no installation.
"""
import struct
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'work'
BASE = Path('C:/Games/Labyrinth Of The Demon King/Shinigami/Content/Paks/pakchunk0-WindowsNoEditor')


class Reader:
    def __init__(self, data): self.data, self.at = data, 0
    def read(self, fmt):
        result = struct.unpack_from('<'+fmt, self.data, self.at)
        self.at += struct.calcsize('<'+fmt)
        return result[0] if len(result) == 1 else result
    def string(self):
        size = self.read('i')
        assert 0 < size < 10000
        value = self.data[self.at:self.at+size]
        self.at += size
        assert value[-1] == 0
        return value[:-1].decode('utf-8')


def main():
    data = BASE.with_suffix('.utoc').read_bytes()
    assert data[:16] == b'-==--==--==--==-'
    assert data[16] == 3 and data[80] == 8  # v3, indexed only
    header, count, block_count, block_size, methods, method_width, compression_size, dirsize, partitions = struct.unpack_from('<9I',data,20)
    assert (header, block_size, methods, partitions) == (144,12,0,1)
    chunks_at = header + count*12
    chunks = [(int.from_bytes(data[chunks_at+i*10:chunks_at+i*10+5],'big'),
               int.from_bytes(data[chunks_at+i*10+5:chunks_at+i*10+10],'big')) for i in range(count)]
    blocks_at = chunks_at + count*10
    directory_at = blocks_at + block_count*12
    r = Reader(data[directory_at:directory_at+dirsize])
    mount = r.string(); assert mount == '../../../'
    directories = [r.read('4I') for _ in range(r.read('I'))]
    files = [r.read('3I') for _ in range(r.read('I'))]
    strings = [r.string() for _ in range(r.read('I'))]
    assert r.at == dirsize
    paths = {}
    def walk(index, prefix):
        _, child, _, file = directories[index]
        while child != 0xffffffff:
            walk(child, prefix+strings[directories[child][0]]+'/')
            child = directories[child][2]
        while file != 0xffffffff:
            name, next_file, user = files[file]
            paths[prefix+strings[name]] = user
            file = next_file
    walk(0, '')
    (ROOT/'iostore-files.txt').write_text('\n'.join(paths),encoding='utf-8')
    with BASE.with_suffix('.ucas').open('rb') as f:
        for name,index in paths.items():
            if not re.search('E_SupportedLanguages|UI_Language|BP_LotDK_GameInstance|UI_Settings_General|ShipporiMinchoB1-Regular_Font|EBGaramond-Regular|EBGaramond-VariableFont_wght_Font',name):continue
            offset,length = chunks[index]
            out=bytearray()
            for block in range(offset//compression_size, (offset+length-1)//compression_size+1):
                b=data[blocks_at+12*block:blocks_at+12*(block+1)]
                physical=int.from_bytes(b[:5],'little');csize=int.from_bytes(b[5:8],'little');usize=int.from_bytes(b[8:11],'little')
                assert b[11] == 0 and csize == usize
                f.seek(physical);raw=f.read(csize);assert len(raw)==csize
                start=max(0,offset-block*compression_size)
                end=min(usize,offset+length-block*compression_size)
                out+=raw[start:end]
            assert len(out)==length
            target=ROOT/'iostore'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(out)
            print(name, length)
            readable=[s.decode('ascii') for s in re.findall(rb'[ -~]{4,}',out)]
            (target.with_suffix('.strings.txt')).write_text('\n'.join(readable),encoding='utf-8')
            print('\n'.join(s for s in readable if re.search('Culture|Language|English|Polish|French|Font|DisplayName|Array|Switch',s,re.I)))


if __name__ == '__main__':main()
