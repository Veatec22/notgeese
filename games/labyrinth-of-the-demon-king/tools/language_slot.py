"""Append Polish to the localization-only language slot widget's default map."""
import struct
from locres import read_string, write_string

PATH='Shinigami/Content/Blueprints/Widgets/LanguageSelectScreen/UI_LanguageSlot.uasset'

def patch(original):
    data=bytearray(original)
    no,ns,ho,hs,io,eo,bo,go,gs=struct.unpack_from('<9i',data,24)
    names=[];at=no
    while at<no+ns:
        size=int.from_bytes(data[at:at+2],'big');at+=2
        wide=bool(size&0x8000);size&=0x7fff
        length=size*(2 if wide else 1)
        names.append(data[at:at+length].decode('utf-16-le' if wide else 'utf-8'));at+=length
    count=(bo-eo)//72;assert eo+count*72==bo
    exports=[struct.unpack_from('<QQI',data,eo+i*72) for i in range(count)]
    bundles=(go-bo)//8-2*count;assert bundles>0
    cursor=go+gs;bounds={}
    for at in range(bo+bundles*8,go,8):
        index,command=struct.unpack_from('<II',data,at)
        if command==1:
            bounds[index]=(cursor,cursor+exports[index][1]);cursor+=exports[index][1]
    assert cursor==len(data)
    target=next(i for i,x in enumerate(exports) if names[x[2]]=='Default__UI_LanguageSlot_C')
    start,end=bounds[target]
    tag=struct.pack('<IIII',names.index('LanguageStrings'),0,names.index('MapProperty'),0)
    at=data.find(tag,start,end);assert at>=0 and data.find(tag,at+1,end)==-1
    size=struct.unpack_from('<I',data,at+16)[0]
    assert data[at+24:at+40]==struct.pack('<IIII',names.index('StrProperty'),0,names.index('TextProperty'),0)
    assert data[at+40]==0
    body=at+41;assert struct.unpack_from('<I',data,body)[0]==0
    number=struct.unpack_from('<I',data,body+4)[0]
    pos=body+8;labels={}
    for _ in range(number):
        code,pos=read_string(data,pos)
        assert data[pos:pos+9]==bytes.fromhex('02000000ff01000000');pos+=9
        label,pos=read_string(data,pos);labels[code]=label
    assert pos==body+size and 'en' in labels and 'pl' not in labels
    added=write_string('pl')+bytes.fromhex('02000000ff01000000')+write_string('Polski')
    delta=len(added)
    struct.pack_into('<I',data,at+16,size+delta)
    struct.pack_into('<I',data,body+4,number+1)
    for i,(offset,length,name) in enumerate(exports):
        if i==target:struct.pack_into('<Q',data,eo+i*72+8,length+delta)
        elif offset>exports[target][0]:struct.pack_into('<Q',data,eo+i*72,offset+delta)
    data[pos:pos]=added
    # The existing map entries and all serialization beyond insertion remain exact.
    assert data[body+8:pos]==original[body+8:pos]
    assert data[pos+delta:]==original[pos:]
    return bytes(data), {'previous_languages':labels,'added':{'pl':'Polski'},'carrier_bytes':len(data)}
